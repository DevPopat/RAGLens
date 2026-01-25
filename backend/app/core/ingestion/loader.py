"""Bitext dataset loader with CSV support."""
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class BitetDatasetLoader:
    """Loader for Bitext Customer Support dataset.

    Supports both JSON and CSV formats with flags, category, intent metadata.
    """

    # CSV format (recommended - includes flags)
    DATASET_CSV_URL = "https://raw.githubusercontent.com/bitext/customer-support-llm-chatbot-training-dataset/main/Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv"

    # JSON format (fallback)
    DATASET_JSON_URL = "https://raw.githubusercontent.com/bitext/customer-support-llm-chatbot-training-dataset/main/Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.json"

    def __init__(self, raw_data_path: str = "/app/data/raw", use_csv: bool = True):
        """Initialize loader.

        Args:
            raw_data_path: Directory to store raw dataset
            use_csv: Use CSV format (includes flags) vs JSON
        """
        self.raw_data_path = Path(raw_data_path)
        self.raw_data_path.mkdir(parents=True, exist_ok=True)
        self.use_csv = use_csv

        if use_csv:
            self.dataset_file = self.raw_data_path / "bitext_customer_support.csv"
            self.dataset_url = self.DATASET_CSV_URL
        else:
            self.dataset_file = self.raw_data_path / "bitext_customer_support.json"
            self.dataset_url = self.DATASET_JSON_URL

    async def download_dataset(self) -> Path:
        """Download Bitext dataset from GitHub.

        Returns:
            Path to downloaded file
        """
        if self.dataset_file.exists():
            logger.info(f"Dataset already exists at {self.dataset_file}")
            return self.dataset_file

        logger.info(f"Downloading Bitext dataset from {self.dataset_url}")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(self.dataset_url)
            response.raise_for_status()

            # Save to file
            with open(self.dataset_file, "wb") as f:
                f.write(response.content)

        logger.info(f"Dataset downloaded to {self.dataset_file}")
        return self.dataset_file

    def load_dataset(self) -> List[Dict[str, Any]]:
        """Load dataset from file (CSV or JSON).

        Returns:
            List of Q&A dictionaries with schema:
            {
                "flags": str,           # Lexical/syntactic/register tags (e.g., "BQZ")
                "instruction": str,     # Customer query/question
                "category": str,        # High-level category (e.g., "ORDER")
                "intent": str,          # Specific intent (e.g., "cancel_order")
                "response": str         # Expected agent response
            }
        """
        if not self.dataset_file.exists():
            raise FileNotFoundError(
                f"Dataset not found at {self.dataset_file}. Run download_dataset() first."
            )

        logger.info(f"Loading dataset from {self.dataset_file}")

        if self.use_csv:
            items = self._load_csv()
        else:
            items = self._load_json()

        logger.info(f"Loaded {len(items)} Q&A pairs from dataset")

        # Log sample statistics
        if items:
            categories = set(item.get("category", "unknown") for item in items)
            intents = set(item.get("intent", "unknown") for item in items)
            flags_set = set(item.get("flags", "") for item in items if item.get("flags"))
            logger.info(f"Dataset contains {len(categories)} categories, {len(intents)} intents, {len(flags_set)} unique flag combinations")

        return items

    def _load_csv(self) -> List[Dict[str, Any]]:
        """Load dataset from CSV file.

        CSV schema: flags,instruction,category,intent,response
        """
        items = []

        with open(self.dataset_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Clean up the row
                item = {
                    "flags": row.get("flags", "").strip(),
                    "instruction": row.get("instruction", "").strip(),
                    "category": row.get("category", "unknown").strip().upper(),
                    "intent": row.get("intent", "unknown").strip().lower(),
                    "response": row.get("response", "").strip()
                }
                items.append(item)

        return items

    def _load_json(self) -> List[Dict[str, Any]]:
        """Load dataset from JSON file (fallback, may not have flags)."""
        with open(self.dataset_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle different possible JSON structures
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and "data" in data:
            items = data["data"]
        else:
            items = list(data.values()) if isinstance(data, dict) else []

        # Normalize schema to match CSV
        normalized = []
        for item in items:
            normalized.append({
                "flags": item.get("flags", ""),
                "instruction": item.get("instruction", item.get("question", "")),
                "category": item.get("category", "unknown").upper(),
                "intent": item.get("intent", "unknown").lower(),
                "response": item.get("response", item.get("answer", ""))
            })

        return normalized

    async def load_or_download(self) -> List[Dict[str, Any]]:
        """Load dataset, downloading if necessary.

        Returns:
            List of Q&A dictionaries
        """
        if not self.dataset_file.exists():
            await self.download_dataset()

        return self.load_dataset()

    def get_dataset_stats(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get comprehensive statistics about the dataset.

        Args:
            items: List of Q&A items

        Returns:
            Dictionary with dataset statistics including flag analysis
        """
        if not items:
            return {"total": 0}

        categories = {}
        intents = {}
        flags_dict = {}
        flag_tags = {
            # Lexical
            "M": 0,  # Morphological
            "L": 0,  # Semantic
            # Syntactic
            "B": 0,  # Basic
            "I": 0,  # Interrogative
            "C": 0,  # Coordinated
            "N": 0,  # Negation
            # Register
            "P": 0,  # Politeness
            "Q": 0,  # Colloquial
            "W": 0,  # Offensive
            # Stylistic
            "K": 0,  # Keyword
            "E": 0,  # Abbreviations
            "Z": 0,  # Errors/Typos
        }

        for item in items:
            category = item.get("category", "unknown")
            intent = item.get("intent", "unknown")
            flags = item.get("flags", "")

            categories[category] = categories.get(category, 0) + 1
            intents[intent] = intents.get(intent, 0) + 1

            if flags:
                flags_dict[flags] = flags_dict.get(flags, 0) + 1
                # Count individual flag tags
                for tag in flags:
                    if tag in flag_tags:
                        flag_tags[tag] += 1

        return {
            "total": len(items),
            "categories": {
                "count": len(categories),
                "breakdown": sorted(categories.items(), key=lambda x: x[1], reverse=True)
            },
            "intents": {
                "count": len(intents),
                "top_10": sorted(intents.items(), key=lambda x: x[1], reverse=True)[:10]
            },
            "flags": {
                "unique_combinations": len(flags_dict),
                "top_10": sorted(flags_dict.items(), key=lambda x: x[1], reverse=True)[:10],
                "tag_distribution": sorted(flag_tags.items(), key=lambda x: x[1], reverse=True)
            }
        }

    def parse_flags(self, flags: str) -> Dict[str, List[str]]:
        """Parse flag string into categories.

        Args:
            flags: Flag string like "BQZ"

        Returns:
            Dict with categorized flags:
            {
                "lexical": ["M", "L"],
                "syntactic": ["B", "I", "C", "N"],
                "register": ["P", "Q", "W"],
                "stylistic": ["K", "E", "Z"]
            }
        """
        lexical = []
        syntactic = []
        register = []
        stylistic = []

        for tag in flags:
            if tag in ["M", "L"]:
                lexical.append(tag)
            elif tag in ["B", "I", "C", "N"]:
                syntactic.append(tag)
            elif tag in ["P", "Q", "W"]:
                register.append(tag)
            elif tag in ["K", "E", "Z"]:
                stylistic.append(tag)

        return {
            "lexical": lexical,
            "syntactic": syntactic,
            "register": register,
            "stylistic": stylistic
        }
