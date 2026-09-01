package com.andrus.myexpenses.domain.model

data class Budget(
    val id: String,
    val categoryId: String,
    val categoryName: String,
    val amountMinor: Long,
    val currency: String,
    val period: String,
    val startDate: String,
    val endDate: String,
    val spentMinor: Long,
    val remainingMinor: Long,
    val usagePercent: Double,
    val thresholdsReached: Set<Int>,
)

data class BudgetDraft(
    val categoryId: String,
    val amountMinor: Long,
    val period: String,
    val startDate: String,
    val endDate: String,
)

enum class BudgetLevel { NORMAL, WARNING, EXCEEDED }

fun budgetLevel(usagePercent: Double): BudgetLevel = when {
    usagePercent >= 100.0 -> BudgetLevel.EXCEEDED
    usagePercent >= 80.0 -> BudgetLevel.WARNING
    else -> BudgetLevel.NORMAL
}
