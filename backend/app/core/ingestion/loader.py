"""Bitext dataset loader with CSV support and stratified splitting."""
import csv
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import random

logger = logging.getLogger(__name__)


class BitetDatasetLoader:
    """Loader for Bitext Customer Support dataset.

    Supports both JSON and CSV formats with flags, category, intent metadata.
    Dataset must be provided locally - no automatic downloading.
    """

    def __init__(self, raw_data_path: str = "/app/data/raw", use_csv: bool = True):
        """Initialize loader.

        Args:
            raw_data_path: Directory containing the dataset
            use_csv: Use CSV format (includes flags) vs JSON
        """
        self.raw_data_path = Path(raw_data_path)
        self.raw_data_path.mkdir(parents=True, exist_ok=True)
        self.use_csv = use_csv

        if use_csv:
            self.dataset_file = self.raw_data_path / "bitext_customer_support.csv"
        else:
            self.dataset_file = self.raw_data_path / "bitext_customer_support.json"

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
                f"Dataset not found at {self.dataset_file}. "
                f"Please place your bitext_customer_support.csv file in {self.raw_data_path}"
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

    def load(self) -> List[Dict[str, Any]]:
        """Load dataset from local file.

        Returns:
            List of Q&A dictionaries

        Raises:
            FileNotFoundError: If dataset file doesn't exist
        """
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

    def add_source_ids(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add unique source_id to each item for tracking.

        Args:
            items: List of Q&A items

        Returns:
            Items with source_id added
        """
        for i, item in enumerate(items):
            # Create unique ID from content hash
            content = f"{item['instruction']}|{item['response']}"
            source_id = hashlib.md5(content.encode()).hexdigest()[:12]
            item["source_id"] = f"doc_{source_id}"
            item["original_index"] = i

        return items

    def stratified_split(
        self,
        items: List[Dict[str, Any]],
        test_size: float = 0.2,
        random_seed: int = 42
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Split dataset into train/test with stratification by category+intent.

        Ensures both sets have proportional representation of all category/intent combos.

        Args:
            items: List of Q&A items (should have source_id added)
            test_size: Fraction for test set (default 0.2 = 20%)
            random_seed: For reproducibility

        Returns:
            Tuple of (train_items, test_items)
        """
        random.seed(random_seed)

        # Group items by stratification key (category + intent)
        groups = defaultdict(list)
        for item in items:
            strat_key = f"{item.get('category', 'unknown')}_{item.get('intent', 'unknown')}"
            groups[strat_key].append(item)

        train_items = []
        test_items = []

        # Split each group proportionally
        for strat_key, group_items in groups.items():
            random.shuffle(group_items)

            # Calculate split point
            n_test = max(1, int(len(group_items) * test_size))

            # Ensure at least 1 in train if group has more than 1 item
            if len(group_items) > 1 and n_test >= len(group_items):
                n_test = len(group_items) - 1

            test_items.extend(group_items[:n_test])
            train_items.extend(group_items[n_test:])

        logger.info(
            f"Stratified split: {len(train_items)} train, {len(test_items)} test "
            f"({len(test_items)/(len(train_items)+len(test_items))*100:.1f}% test)"
        )

        # Log distribution check
        train_categories = defaultdict(int)
        test_categories = defaultdict(int)
        for item in train_items:
            train_categories[item.get("category", "unknown")] += 1
        for item in test_items:
            test_categories[item.get("category", "unknown")] += 1

        logger.info(f"Train categories: {dict(train_categories)}")
        logger.info(f"Test categories: {dict(test_categories)}")

        return train_items, test_items

    def save_split(
        self,
        train_items: List[Dict[str, Any]],
        test_items: List[Dict[str, Any]],
        output_dir: str = None
    ) -> Tuple[Path, Path]:
        """Save train and test splits to separate files.

        Args:
            train_items: Training data
            test_items: Test/holdout data
            output_dir: Output directory (default: raw_data_path)

        Returns:
            Tuple of (train_file_path, test_file_path)
        """
        output_dir = Path(output_dir) if output_dir else self.raw_data_path

        train_file = output_dir / "bitext_train.json"
        test_file = output_dir / "bitext_test_holdout.json"

        with open(train_file, "w", encoding="utf-8") as f:
            json.dump(train_items, f, indent=2)
        logger.info(f"Saved {len(train_items)} training items to {train_file}")

        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(test_items, f, indent=2)
        logger.info(f"Saved {len(test_items)} test items to {test_file}")

        return train_file, test_file

    def load_split(
        self,
        split: str = "train",
        output_dir: str = None
    ) -> List[Dict[str, Any]]:
        """Load a previously saved split.

        Args:
            split: "train" or "test"
            output_dir: Directory containing split files

        Returns:
            List of items from the requested split
        """
        output_dir = Path(output_dir) if output_dir else self.raw_data_path

        if split == "train":
            file_path = output_dir / "bitext_train.json"
        elif split == "test":
            file_path = output_dir / "bitext_test_holdout.json"
        else:
            raise ValueError(f"Invalid split: {split}. Use 'train' or 'test'")

        if not file_path.exists():
            raise FileNotFoundError(
                f"Split file not found: {file_path}. Run stratified_split() first."
            )

        with open(file_path, "r", encoding="utf-8") as f:
            items = json.load(f)

        logger.info(f"Loaded {len(items)} items from {split} split")
        return items

    def load_and_split(
        self,
        test_size: float = 0.2,
        random_seed: int = 42,
        force_resplit: bool = False
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Load dataset, add source IDs, and split into train/test.

        This is the main method to use for preparing data for RAG + evaluation.

        Args:
            test_size: Fraction for test set
            random_seed: For reproducibility
            force_resplit: Re-split even if split files exist

        Returns:
            Tuple of (train_items, test_items)

        Raises:
            FileNotFoundError: If dataset file doesn't exist
        """
        train_file = self.raw_data_path / "bitext_train.json"
        test_file = self.raw_data_path / "bitext_test_holdout.json"

        # Use cached splits if available
        if train_file.exists() and test_file.exists() and not force_resplit:
            logger.info("Loading existing train/test splits")
            train_items = self.load_split("train")
            test_items = self.load_split("test")
            return train_items, test_items

        # Load full dataset
        items = self.load_dataset()

        # Add source IDs for tracking
        items = self.add_source_ids(items)

        # Stratified split
        train_items, test_items = self.stratified_split(
            items,
            test_size=test_size,
            random_seed=random_seed
        )

        # Save splits
        self.save_split(train_items, test_items)

        return train_items, test_items

    def get_source_ids_by_category_intent(
        self,
        items: List[Dict[str, Any]],
        category: str,
        intent: str
    ) -> List[str]:
        """Get all source_ids matching a category and intent.

        Useful for finding relevant docs during evaluation.

        Args:
            items: List of items (typically training set)
            category: Category to match
            intent: Intent to match

        Returns:
            List of source_ids
        """
        return [
            item["source_id"]
            for item in items
            if item.get("category", "").upper() == category.upper()
            and item.get("intent", "").lower() == intent.lower()
            and "source_id" in item
        ]
