package com.andrus.myexpenses.tasks

import java.time.Instant
import java.time.ZoneOffset
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class SubscriptionNotificationWorkerTest {
    @Test
    fun `notification delay targets nine o'clock before payment`() {
        val now = Instant.parse("2026-08-20T06:00:00Z")
        val delay = notificationDelayMillis("2026-08-24", 3, now, ZoneOffset.UTC)

        assertEquals(27 * 60 * 60 * 1000L, delay)
    }

    @Test
    fun `past notification is not scheduled`() {
        assertNull(
            notificationDelayMillis(
                "2026-08-20",
                1,
                Instant.parse("2026-08-20T10:00:00Z"),
                ZoneOffset.UTC,
            ),
        )
    }
}
