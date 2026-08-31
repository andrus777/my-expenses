package com.andrus.myexpenses.domain.model

data class Subscription(
    val id: String,
    val categoryId: String,
    val name: String,
    val amountMinor: Long,
    val currency: String,
    val frequency: String,
    val customIntervalDays: Int?,
    val nextPaymentDate: String,
    val comment: String?,
    val isActive: Boolean,
)

data class SubscriptionPayment(
    val id: String,
    val subscriptionId: String,
    val expenseId: String,
    val paymentDate: String,
    val amountMinor: Long,
)

data class SubscriptionDraft(
    val name: String,
    val categoryId: String,
    val amountMinor: Long,
    val frequency: String,
    val customIntervalDays: Int?,
    val nextPaymentDate: String,
)
