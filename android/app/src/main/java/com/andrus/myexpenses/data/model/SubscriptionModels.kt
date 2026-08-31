package com.andrus.myexpenses.data.model

data class SubscriptionDto(
    val id: String,
    val category_id: String,
    val name: String,
    val amount: String,
    val currency: String,
    val frequency: String,
    val custom_interval_days: Int?,
    val next_payment_date: String,
    val comment: String?,
    val is_active: Boolean,
)

data class SubscriptionRequest(
    val name: String,
    val category_id: String,
    val amount: String,
    val currency: String = "RUB",
    val frequency: String,
    val custom_interval_days: Int?,
    val next_payment_date: String,
)

data class SubscriptionResponse(val subscription: SubscriptionDto)
data class SubscriptionListResponse(val items: List<SubscriptionDto>)
data class PaymentRequest(val client_operation_id: String, val payment_date: String)
data class PaymentDto(
    val id: String,
    val subscription_id: String,
    val expense_id: String,
    val payment_date: String,
    val amount: String,
)
data class PaymentResponse(val payment: PaymentDto, val subscription: SubscriptionDto)
data class PaymentListResponse(val items: List<PaymentDto>)
