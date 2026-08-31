package com.andrus.myexpenses.domain.repository

import com.andrus.myexpenses.domain.model.Subscription
import com.andrus.myexpenses.domain.model.SubscriptionDraft
import com.andrus.myexpenses.domain.model.SubscriptionPayment
import kotlinx.coroutines.flow.StateFlow

interface SubscriptionRepository {
    val subscriptions: StateFlow<List<Subscription>>
    val payments: StateFlow<List<SubscriptionPayment>>
    suspend fun refresh()
    suspend fun save(id: String?, draft: SubscriptionDraft)
    suspend fun delete(id: String)
    suspend fun markPaid(id: String)
    suspend fun loadPayments(id: String)
}

fun interface SubscriptionNotificationScheduler {
    fun schedule(subscriptions: List<Subscription>)
}
