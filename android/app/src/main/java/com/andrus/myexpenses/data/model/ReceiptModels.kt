package com.andrus.myexpenses.data.model

data class ReceiptJobRequest(val receipt_data: String)
data class ReceiptJobCreated(val job_id: String, val status: String)
data class ReceiptItemDto(val name: String, val quantity: String, val price: String, val total: String)
data class ReceiptDto(
    val id: String,
    val merchant: String,
    val total: String,
    val currency: String,
    val purchase_date: String,
    val items: List<ReceiptItemDto>,
    val finalized: Boolean,
    val expense_id: String?,
)
data class ReceiptErrorDto(val code: String, val message: String)
data class ReceiptJobDto(
    val job_id: String,
    val status: String,
    val attempts: Int,
    val error: ReceiptErrorDto?,
    val receipt: ReceiptDto?,
)
data class ReceiptFinalizeRequest(val category_id: String, val client_operation_id: String)
