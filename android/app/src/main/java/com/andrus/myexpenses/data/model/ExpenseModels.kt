package com.andrus.myexpenses.data.model

data class CategoryDto(val id: String, val name: String, val is_system: Boolean)

data class CategoryListResponse(val items: List<CategoryDto>)

data class ExpenseDto(
    val id: String,
    val category_id: String,
    val amount: String,
    val currency: String,
    val expense_date: String,
    val merchant: String?,
    val description: String?,
    val comment: String?,
    val source: String,
    val client_operation_id: String,
    val created_at: String,
    val updated_at: String,
)

data class ExpenseRequest(
    val category_id: String,
    val amount: String,
    val currency: String,
    val expense_date: String,
    val merchant: String?,
    val description: String?,
    val comment: String?,
    val source: String,
    val client_operation_id: String,
)

data class ExpensePatchRequest(
    val category_id: String,
    val amount: String,
    val currency: String,
    val expense_date: String,
    val merchant: String?,
    val description: String?,
    val comment: String?,
)

data class ExpenseResponse(val expense: ExpenseDto)

data class PaginationDto(val page: Int, val pages: Int)

data class ExpenseListResponse(val items: List<ExpenseDto>, val pagination: PaginationDto)
