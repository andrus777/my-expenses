package com.andrus.myexpenses.data.repository

import com.andrus.myexpenses.data.model.*
import com.andrus.myexpenses.data.remote.ResponseMapper
import com.andrus.myexpenses.data.remote.SubscriptionApi
import com.andrus.myexpenses.domain.model.*
import com.andrus.myexpenses.domain.repository.SubscriptionNotificationScheduler
import com.andrus.myexpenses.domain.repository.SubscriptionRepository
import java.math.BigDecimal
import java.time.LocalDate
import java.util.UUID
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class DefaultSubscriptionRepository(
    private val api: SubscriptionApi,
    private val responses: ResponseMapper,
    private val notifications: SubscriptionNotificationScheduler,
) : SubscriptionRepository {
    private val mutableSubscriptions = MutableStateFlow<List<Subscription>>(emptyList())
    override val subscriptions = mutableSubscriptions.asStateFlow()
    private val mutablePayments = MutableStateFlow<List<SubscriptionPayment>>(emptyList())
    override val payments = mutablePayments.asStateFlow()

    override suspend fun refresh() {
        mutableSubscriptions.value = responses.requireBody(api.list()).items.map { it.domain() }
        notifications.schedule(mutableSubscriptions.value)
    }

    override suspend fun save(id: String?, draft: SubscriptionDraft) {
        val request = draft.request()
        if (id == null) responses.requireBody(api.create(request)) else responses.requireBody(api.update(id, request))
        refresh()
    }

    override suspend fun delete(id: String) {
        val response = api.delete(id)
        if (!response.isSuccessful) responses.requireBody(response)
        refresh()
    }

    override suspend fun markPaid(id: String) {
        responses.requireBody(api.pay(id, PaymentRequest(UUID.randomUUID().toString(), LocalDate.now().toString())))
        refresh()
        loadPayments(id)
    }

    override suspend fun loadPayments(id: String) {
        mutablePayments.value = responses.requireBody(api.payments(id)).items.map { it.domain() }
    }
}

private fun SubscriptionDraft.request() = SubscriptionRequest(
    name, categoryId, BigDecimal.valueOf(amountMinor, 2).toPlainString(), frequency = frequency,
    custom_interval_days = customIntervalDays, next_payment_date = nextPaymentDate,
)
private fun SubscriptionDto.domain() = Subscription(
    id, category_id, name, BigDecimal(amount).movePointRight(2).longValueExact(), currency,
    frequency, custom_interval_days, next_payment_date, comment, is_active,
)
private fun PaymentDto.domain() = SubscriptionPayment(
    id, subscription_id, expense_id, payment_date, BigDecimal(amount).movePointRight(2).longValueExact(),
)
