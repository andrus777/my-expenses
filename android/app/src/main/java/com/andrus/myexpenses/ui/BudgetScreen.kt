package com.andrus.myexpenses.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.andrus.myexpenses.domain.model.*
import com.andrus.myexpenses.presentation.BudgetViewModel
import java.math.BigDecimal

@Composable
fun BudgetScreen(viewModel: BudgetViewModel, onAdd: () -> Unit, onEdit: (String) -> Unit) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    Scaffold(
        floatingActionButton = { FloatingActionButton(onClick = onAdd) { Text("+") } },
    ) { padding ->
        Column(Modifier.padding(padding).padding(16.dp)) {
            Text("Бюджеты", style = MaterialTheme.typography.headlineMedium)
            state.thresholdEvent?.let { AssistChip(onClick = {}, label = { Text(it) }) }
            when {
                state.loading -> LinearProgressIndicator(Modifier.fillMaxWidth())
                state.error != null -> Column { Text(state.error!!, color = MaterialTheme.colorScheme.error); Button(onClick = viewModel::refresh) { Text("Повторить") } }
                state.budgets.isEmpty() -> Text("Бюджетов пока нет")
                else -> LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(state.budgets, key = { it.id }) { BudgetCard(it, Modifier.clickable { onEdit(it.id) }) }
                }
            }
        }
    }
}

@Composable
fun BudgetSummary(budgets: List<Budget>, onOpen: () -> Unit) {
    if (budgets.isEmpty()) {
        TextButton(onClick = onOpen) { Text("Настроить бюджет") }
        return
    }
    Column {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Бюджеты", style = MaterialTheme.typography.titleMedium)
            TextButton(onClick = onOpen) { Text("Все") }
        }
        budgets.take(2).forEach { BudgetCard(it) }
    }
}

@Composable
private fun BudgetCard(budget: Budget, modifier: Modifier = Modifier) {
    val level = budgetLevel(budget.usagePercent)
    val color = when (level) {
        BudgetLevel.NORMAL -> MaterialTheme.colorScheme.primary
        BudgetLevel.WARNING -> Color(0xFFB26A00)
        BudgetLevel.EXCEEDED -> MaterialTheme.colorScheme.error
    }
    Card(modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(budget.categoryName)
                Text("${budget.spentMinor.money()} / ${budget.amountMinor.money()} ${budget.currency}", color = color)
            }
            LinearProgressIndicator(
                progress = { (budget.usagePercent / 100).toFloat().coerceIn(0f, 1f) },
                modifier = Modifier.fillMaxWidth(), color = color,
            )
            if (level == BudgetLevel.WARNING) Text("Приближается к лимиту", color = color)
            if (level == BudgetLevel.EXCEEDED) Text("Лимит исчерпан", color = color)
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BudgetForm(viewModel: BudgetViewModel, budget: Budget?, onDone: () -> Unit) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var amount by remember(budget?.id) { mutableStateOf(budget?.amountMinor?.money().orEmpty()) }
    var categoryId by remember(budget?.id) { mutableStateOf(budget?.categoryId.orEmpty()) }
    var period by remember(budget?.id) { mutableStateOf(budget?.period ?: "MONTH") }
    var start by remember(budget?.id) { mutableStateOf(budget?.startDate ?: java.time.LocalDate.now().withDayOfMonth(1).toString()) }
    var end by remember(budget?.id) { mutableStateOf(budget?.endDate ?: java.time.LocalDate.now().withDayOfMonth(java.time.LocalDate.now().lengthOfMonth()).toString()) }
    var categoryMenu by remember { mutableStateOf(false) }
    var periodMenu by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    Scaffold(topBar = { TopAppBar(title = { Text(if (budget == null) "Новый бюджет" else "Редактировать бюджет") }) }) { padding ->
        Column(Modifier.padding(padding).padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Box { Button(onClick = { categoryMenu = true }) { Text(state.categories.firstOrNull { it.id == categoryId }?.name ?: "Категория") }; DropdownMenu(categoryMenu, { categoryMenu = false }) { state.categories.forEach { DropdownMenuItem({ Text(it.name) }, { categoryId = it.id; categoryMenu = false }) } } }
            OutlinedTextField(amount, { amount = it }, Modifier.fillMaxWidth(), label = { Text("Лимит") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal))
            Box { Button(onClick = { periodMenu = true }) { Text(periodLabel(period)) }; DropdownMenu(periodMenu, { periodMenu = false }) { listOf("WEEK", "MONTH", "YEAR", "CUSTOM").forEach { value -> DropdownMenuItem({ Text(periodLabel(value)) }, { period = value; periodMenu = false }) } } }
            OutlinedTextField(start, { start = it }, Modifier.fillMaxWidth(), label = { Text("Начало YYYY-MM-DD") })
            OutlinedTextField(end, { end = it }, Modifier.fillMaxWidth(), label = { Text("Окончание YYYY-MM-DD") })
            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            Button({ error = viewModel.save(budget?.id, categoryId, amount, period, start, end); if (error == null) onDone() }, Modifier.fillMaxWidth()) { Text("Сохранить") }
            if (budget != null) TextButton({ viewModel.delete(budget.id); onDone() }) { Text("Удалить") }
        }
    }
}

private fun periodLabel(period: String) = mapOf("WEEK" to "Неделя", "MONTH" to "Месяц", "YEAR" to "Год", "CUSTOM" to "Произвольный")[period] ?: period
private fun Long.money() = BigDecimal.valueOf(this, 2).toPlainString()
