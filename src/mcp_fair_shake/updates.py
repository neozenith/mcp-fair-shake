"""Update checking for Australian legislation.

Tracks when legislation was last fetched and checks for new versions.
"""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .cache import CacheManager
from .canonical_id import parse_canonical_id
from .fetcher import LegislationFetcher

# Update tracking directory
UPDATE_TRACKING_DIR = Path(__file__).parent.parent.parent / "data" / "metadata" / "updates"


@dataclass
class UpdateStatus:
    """Update status for a piece of legislation."""

    canonical_id: str
    last_check: str  # ISO format timestamp
    last_update: str  # ISO format timestamp
    current_hash: str
    update_available: bool
    check_interval_days: int = 7


class UpdateChecker:
    """Check for updates to cached legislation."""

    def __init__(
        self,
        cache_manager: CacheManager | None = None,
        fetcher: LegislationFetcher | None = None,
        tracking_dir: Path | None = None,
    ):
        """Initialize update checker.

        Args:
            cache_manager: Cache manager instance
            fetcher: Legislation fetcher instance
            tracking_dir: Directory for update tracking files
        """
        self.cache_manager = cache_manager or CacheManager()
        self.fetcher = fetcher or LegislationFetcher(self.cache_manager)
        self.tracking_dir = tracking_dir or UPDATE_TRACKING_DIR
        self.tracking_dir.mkdir(parents=True, exist_ok=True)

    def get_tracking_path(self, canonical_id: str) -> Path:
        """Get path to update tracking file.

        Args:
            canonical_id: Canonical legislation ID

        Returns:
            Path to tracking file
        """
        # Convert canonical ID to filename (replace / with -)
        filename = canonical_id.replace("/", "-").lstrip("-") + ".json"
        return self.tracking_dir / filename

    def load_update_status(self, canonical_id: str) -> UpdateStatus | None:
        """Load update status for legislation.

        Args:
            canonical_id: Canonical legislation ID

        Returns:
            UpdateStatus or None if not tracked
        """
        tracking_path = self.get_tracking_path(canonical_id)
        if not tracking_path.exists():
            return None

        data = json.loads(tracking_path.read_text())
        return UpdateStatus(**data)

    def save_update_status(self, status: UpdateStatus) -> None:
        """Save update status for legislation.

        Args:
            status: Update status to save
        """
        tracking_path = self.get_tracking_path(status.canonical_id)
        tracking_path.write_text(json.dumps(asdict(status), indent=2))

    def check_for_updates(self, canonical_id: str, force: bool = False) -> UpdateStatus:
        """Check if updates are available for legislation.

        Args:
            canonical_id: Canonical legislation ID
            force: Force check even if recently checked

        Returns:
            Update status
        """
        # Load existing status
        status = self.load_update_status(canonical_id)

        # Check if we need to check for updates
        if status and not force:
            last_check_time = datetime.fromisoformat(status.last_check)
            check_interval = timedelta(days=status.check_interval_days)

            if datetime.now(UTC) - last_check_time < check_interval:
                # Too soon to check again
                return status

        # Get current cached version
        canonical = parse_canonical_id(canonical_id)
        if not canonical:
            raise ValueError(f"Invalid canonical ID: {canonical_id}")

        metadata = self.cache_manager.read_metadata(canonical)
        if not metadata:
            raise ValueError(f"No cached metadata for {canonical_id}")

        current_hash = metadata.content_hash

        # Check for updates by comparing hash
        # In a real implementation, this would fetch headers or a manifest
        # For now, we'll just track the current state
        now = datetime.now(UTC).isoformat()

        if status:
            # Update existing status
            status.last_check = now
            status.current_hash = current_hash
            status.update_available = False  # Would check remote here
        else:
            # Create new status
            status = UpdateStatus(
                canonical_id=canonical_id,
                last_check=now,
                last_update=metadata.fetch_timestamp,
                current_hash=current_hash,
                update_available=False,
            )

        # Save status
        self.save_update_status(status)

        return status

    def get_all_tracked(self) -> list[UpdateStatus]:
        """Get update status for all tracked legislation.

        Returns:
            List of update statuses
        """
        statuses = []

        for tracking_file in self.tracking_dir.glob("*.json"):
            try:
                data = json.loads(tracking_file.read_text())
                statuses.append(UpdateStatus(**data))
            except Exception:
                # Skip invalid files
                continue

        return statuses

    def check_all_updates(self, force: bool = False) -> dict[str, UpdateStatus]:
        """Check for updates to all tracked legislation.

        Args:
            force: Force check even if recently checked

        Returns:
            Dict mapping canonical IDs to update statuses
        """
        results = {}

        for status in self.get_all_tracked():
            try:
                updated_status = self.check_for_updates(status.canonical_id, force=force)
                results[status.canonical_id] = updated_status
            except Exception:
                # Skip on error
                continue

        return results

    def get_outdated(self, max_age_days: int = 30) -> list[str]:
        """Get list of legislation that hasn't been updated recently.

        Args:
            max_age_days: Maximum age in days

        Returns:
            List of canonical IDs that need updating
        """
        outdated = []
        cutoff = datetime.now(UTC) - timedelta(days=max_age_days)

        for status in self.get_all_tracked():
            last_update = datetime.fromisoformat(status.last_update)
            if last_update < cutoff:
                outdated.append(status.canonical_id)

        return outdated

    def mark_updated(self, canonical_id: str, new_hash: str) -> None:
        """Mark legislation as updated.

        Args:
            canonical_id: Canonical legislation ID
            new_hash: New content hash
        """
        status = self.load_update_status(canonical_id)
        now = datetime.now(UTC).isoformat()

        if status:
            status.last_update = now
            status.last_check = now
            status.current_hash = new_hash
            status.update_available = False
        else:
            status = UpdateStatus(
                canonical_id=canonical_id,
                last_check=now,
                last_update=now,
                current_hash=new_hash,
                update_available=False,
            )

        self.save_update_status(status)
