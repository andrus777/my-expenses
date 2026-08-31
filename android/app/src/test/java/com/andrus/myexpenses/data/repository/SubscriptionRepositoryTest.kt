package com.andrus.myexpenses.data.repository

import com.andrus.myexpenses.data.model.SubscriptionDto
import com.andrus.myexpenses.data.model.SubscriptionListResponse
import com.andrus.myexpenses.data.remote.ResponseMapper
import com.andrus.myexpenses.data.remote.SubscriptionApi
import com.andrus.myexpenses.domain.repository.SubscriptionNotificationScheduler
import com.google.gson.Gson
import io.mockk.coEvery
import io.mockk.mockk
import io.mockk.verify
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Test
import retrofit2.Response

class SubscriptionRepositoryTest {
    @Test
    fun `refresh publishes subscriptions and schedules notifications`() = runTest {
        val api = mockk<SubscriptionApi>()
        val scheduler = mockk<SubscriptionNotificationScheduler>(relaxed = true)
        coEvery { api.list() } returns Response.success(
            SubscriptionListResponse(
                listOf(SubscriptionDto("id", "category", "Музыка", "299.00", "RUB", "MONTHLY", null, "2026-09-30", null, true)),
            ),
        )
        val repository = DefaultSubscriptionRepository(api, ResponseMapper(Gson()), scheduler)

        repository.refresh()

        assertEquals(29900, repository.subscriptions.value.single().amountMinor)
        verify { scheduler.schedule(match { it.single().id == "id" }) }
    }
}
