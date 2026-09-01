package com.andrus.myexpenses.data.model

data class BudgetDto(
    val id: String,
    val category_id: String,
    val category_name: String,
    val amount: String,
    val currency: String,
    val period: String,
    val start_date: String,
    val end_date: String,
    val spent: String,
    val remaining: String,
    val usage_percent: String,
    val thresholds_reached: List<Int>,
)

data class BudgetRequest(
    val category_id: String,
    val amount: String,
    val currency: String = "RUB",
    val period: String,
    val start_date: String,
    val end_date: String,
)

data class BudgetResponse(val budget: BudgetDto)
data class BudgetListResponse(val items: List<BudgetDto>)
