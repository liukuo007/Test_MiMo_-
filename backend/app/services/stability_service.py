from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stability import FailureCluster, FlakyTestCase, StabilityTrend
from app.models.test_case import TestCase
from app.models.test_result import TestResult

# Failure classification keywords
FAILURE_CATEGORIES = {
    "mqtt_timeout": ["mqtt", "timeout", "broker", "connect", "publish", "subscribe"],
    "ai_misprediction": ["ai", "predict", "recognize", "confidence", "model", "inference"],
    "payment_failure": ["payment", "pay", "transaction", "charge", "refund", "gateway"],
    "network_error": ["network", "connection", "dns", "socket", "http", "502", "503", "504"],
    "config_issue": ["config", "setting", "env", "environment", "missing", "not found"],
    "data_corruption": ["data", "corrupt", "invalid", "format", "parse", "decode", "encode"],
}


class StabilityService:

    async def detect_flaky_tests(self, db: AsyncSession, lookback_days: int = 7) -> list[FlakyTestCase]:
        """Detect flaky tests: tests that alternate between pass and fail."""
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)

        # Get all test cases with results in the period
        result = await db.execute(
            select(TestResult.test_case_id, TestResult.status, func.count().label("cnt"))
            .where(TestResult.created_at >= cutoff)
            .group_by(TestResult.test_case_id, TestResult.status)
        )

        case_stats: dict[int, dict[str, int]] = defaultdict(lambda: {"passed": 0, "failed": 0})
        for row in result.all():
            if row.test_case_id:
                case_stats[row.test_case_id][row.status] = row.cnt

        flaky_cases = []
        for case_id, stats in case_stats.items():
            total = stats["passed"] + stats["failed"]
            if total < 3:
                continue

            # Flaky: has both passes and fails
            if stats["passed"] > 0 and stats["failed"] > 0:
                flaky_rate = min(stats["passed"], stats["failed"]) / total
                if flaky_rate >= 0.1:  # At least 10% flaky
                    # Check for existing record
                    existing = await db.execute(
                        select(FlakyTestCase).where(
                            FlakyTestCase.test_case_id == case_id,
                            FlakyTestCase.status == "active",
                        )
                    )
                    flaky = existing.scalar_one_or_none()
                    if flaky:
                        flaky.flaky_rate = flaky_rate
                        flaky.pattern = {
                            "type": "pass_fail交替",
                            "pass_count": stats["passed"],
                            "fail_count": stats["failed"],
                            "total": total,
                        }
                    else:
                        flaky = FlakyTestCase(
                            test_case_id=case_id,
                            flaky_rate=flaky_rate,
                            pattern={
                                "type": "pass_fail交替",
                                "pass_count": stats["passed"],
                                "fail_count": stats["failed"],
                                "total": total,
                            },
                        )
                        db.add(flaky)
                    flaky_cases.append(flaky)

        await db.commit()
        return flaky_cases

    async def classify_failure(self, error_message: str) -> str:
        """Classify failure based on keyword matching."""
        if not error_message:
            return "unknown"
        lower = error_message.lower()
        scores: dict[str, int] = {}
        for category, keywords in FAILURE_CATEGORIES.items():
            score = sum(1 for kw in keywords if kw in lower)
            if score > 0:
                scores[category] = score
        if not scores:
            return "unknown"
        return max(scores, key=scores.get)

    async def cluster_failures(self, db: AsyncSession, lookback_days: int = 7) -> list[FailureCluster]:
        """Cluster recent failures by root cause category."""
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)

        result = await db.execute(
            select(TestResult)
            .where(TestResult.status == "failed", TestResult.created_at >= cutoff)
            .limit(1000)
        )
        failures = list(result.scalars().all())

        if not failures:
            return []

        # Classify each failure
        categories: dict[str, list[str]] = defaultdict(list)
        for f in failures:
            error_msg = f.error_message or ""
            cat = await self.classify_failure(error_msg)
            categories[cat].append(error_msg[:200])

        total = len(failures)
        # Clear old clusters
        old = await db.execute(select(FailureCluster))
        for c in old.scalars().all():
            await db.delete(c)

        clusters = []
        for cat, errors in categories.items():
            # Extract common keywords
            all_words = []
            for msg in errors:
                words = msg.lower().split()
                all_words.extend(w for w in words if len(w) > 3)
            common_kw = [w for w, _ in Counter(all_words).most_common(10)]

            cluster = FailureCluster(
                cluster_name=cat,
                root_cause_category=cat,
                sample_count=len(errors),
                percentage=round(len(errors) / total * 100, 1),
                sample_errors={"messages": errors[:5]},
                keywords={"top_keywords": common_kw},
            )
            db.add(cluster)
            clusters.append(cluster)

        await db.commit()
        return clusters

    async def compute_stability_trends(self, db: AsyncSession, lookback_days: int = 7) -> list[StabilityTrend]:
        """Compute stability trends by dimension."""
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)

        # Overall trend
        result = await db.execute(
            select(
                func.count().label("total"),
                func.count().filter(TestResult.status == "passed").label("passed"),
                func.count().filter(TestResult.status == "failed").label("failed"),
            ).where(TestResult.created_at >= cutoff)
        )
        row = result.one()
        total = row.total or 0
        passed = row.passed or 0
        pass_rate = round(passed / total * 100, 1) if total > 0 else 100

        # Get flaky count
        flaky_result = await db.execute(
            select(func.count()).select_from(FlakyTestCase).where(FlakyTestCase.status == "active")
        )
        flaky_count = flaky_result.scalar() or 0
        flaky_rate = round(flaky_count / total * 100, 1) if total > 0 else 0
        stability_score = max(0, 100 - (100 - pass_rate) - flaky_rate)

        # Clear old trends
        old = await db.execute(select(StabilityTrend))
        for t in old.scalars().all():
            await db.delete(t)

        trend = StabilityTrend(
            dimension="overall",
            dimension_value="all",
            stability_score=round(stability_score, 1),
            pass_rate=pass_rate,
            flaky_rate=flaky_rate,
            total_runs=total,
        )
        db.add(trend)
        await db.commit()
        return [trend]

    async def get_flaky_list(self, db: AsyncSession, status: Optional[str] = None) -> list[dict]:
        q = select(FlakyTestCase).order_by(desc(FlakyTestCase.flaky_rate))
        if status:
            q = q.where(FlakyTestCase.status == status)
        result = await db.execute(q)
        cases = list(result.scalars().all())

        # Enrich with test case name
        enriched = []
        for c in cases:
            tc_result = await db.execute(select(TestCase).where(TestCase.id == c.test_case_id))
            tc = tc_result.scalar_one_or_none()
            enriched.append({
                "id": c.id,
                "test_case_id": c.test_case_id,
                "test_case_name": tc.name if tc else None,
                "flaky_rate": c.flaky_rate,
                "pattern": c.pattern,
                "status": c.status,
                "detected_at": c.detected_at,
                "resolved_at": c.resolved_at,
            })
        return enriched

    async def mark_resolved(self, db: AsyncSession, flaky_id: int) -> bool:
        result = await db.execute(select(FlakyTestCase).where(FlakyTestCase.id == flaky_id))
        flaky = result.scalar_one_or_none()
        if not flaky:
            return False
        flaky.status = "resolved"
        flaky.resolved_at = datetime.utcnow()
        await db.commit()
        return True

    async def get_summary(self, db: AsyncSession) -> dict:
        total = await db.execute(select(func.count()).select_from(FlakyTestCase))
        active = await db.execute(
            select(func.count()).select_from(FlakyTestCase).where(FlakyTestCase.status == "active")
        )
        resolved = await db.execute(
            select(func.count()).select_from(FlakyTestCase).where(FlakyTestCase.status == "resolved")
        )
        clusters_result = await db.execute(select(FailureCluster).order_by(desc(FailureCluster.percentage)))
        clusters = list(clusters_result.scalars().all())
        trends_result = await db.execute(select(StabilityTrend))
        trends = list(trends_result.scalars().all())

        overall_score = 100.0
        if trends:
            overall_score = trends[0].stability_score

        return {
            "total_flaky": total.scalar() or 0,
            "active_flaky": active.scalar() or 0,
            "resolved_flaky": resolved.scalar() or 0,
            "overall_stability_score": overall_score,
            "clusters": clusters,
            "trends": trends,
        }


stability_service = StabilityService()
