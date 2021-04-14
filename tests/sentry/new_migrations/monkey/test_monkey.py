from django.db.migrations import executor, writer

from sentry.new_migrations.monkey.executor import SentryMigrationExecutor
from sentry.new_migrations.monkey.writer import SENTRY_MIGRATION_TEMPLATE
from sentry.testutils import TestCase


class MonkeyTest(TestCase):
    def test(self):
        assert executor.MigrationExecutor is SentryMigrationExecutor
        assert writer.MIGRATION_TEMPLATE == SENTRY_MIGRATION_TEMPLATE