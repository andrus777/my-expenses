package com.andrus.myexpenses.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.andrus.myexpenses.domain.model.TimelinePoint
import com.andrus.myexpenses.presentation.StatisticsPeriod
import com.andrus.myexpenses.presentation.StatisticsViewModel
import java.math.BigDecimal
import java.math.RoundingMode

@Composable
fun StatisticsScreen(viewModel: StatisticsViewModel) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var from by remember(state.dateFrom) { mutableStateOf(state.dateFrom) }
    var to by remember(state.dateTo) { mutableStateOf(state.dateTo) }
    var validation by remember { mutableStateOf<String?>(null) }
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("Статистика", style = MaterialTheme.typography.headlineMedium)
        PeriodSelector(state.period, viewModel::selectPeriod)
        if (state.period == StatisticsPeriod.CUSTOM) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(from, { from = it }, Modifier.weight(1f), label = { Text("От") })
                OutlinedTextField(to, { to = it }, Modifier.weight(1f), label = { Text("До") })
            }
            Button(onClick = { validation = viewModel.loadCustom(from, to) }) { Text("Применить") }
            validation?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        }
        when {
            state.loading -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
            state.error != null -> ErrorStatistics(state.error!!, viewModel::retry)
            state.empty -> EmptyStatistics()
            state.data != null -> StatisticsContent(state.data!!)
        }
    }
}

@Composable
private fun PeriodSelector(selected: StatisticsPeriod, select: (StatisticsPeriod) -> Unit) {
    SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth().padding(vertical = 12.dp)) {
        listOf(
            StatisticsPeriod.WEEK to "Неделя",
            StatisticsPeriod.MONTH to "Месяц",
            StatisticsPeriod.YEAR to "Год",
            StatisticsPeriod.CUSTOM to "Свой",
        ).forEachIndexed { index, item ->
            SegmentedButton(
                selected = selected == item.first,
                onClick = { select(item.first) },
                shape = SegmentedButtonDefaults.itemShape(index, 4),
            ) { Text(item.second) }
        }
    }
}

@Composable
private fun StatisticsContent(data: com.andrus.myexpenses.domain.model.StatisticsSnapshot) {
    LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                SummaryCard("Всего", "${data.summary.total.money()} ₽", Modifier.weight(1f))
                SummaryCard("Операций", data.summary.operationsCount.toString(), Modifier.weight(1f))
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                SummaryCard("В среднем/день", "${data.summary.averageDaily.money()} ₽", Modifier.weight(1f))
                val change = data.summary.changePercent?.let { "${if (it.signum() > 0) "+" else ""}${it.money()}%" } ?: "—"
                SummaryCard("К прошлому периоду", change, Modifier.weight(1f))
            }
        }
        item { Text("Динамика", style = MaterialTheme.typography.titleLarge) }
        item { TimelineChart(data.timeline) }
        item { Text("По категориям", style = MaterialTheme.typography.titleLarge) }
        items(data.categories) { category ->
            Column {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(category.name)
                    Text("${category.total.money()} ₽ · ${category.percent.money()}%")
                }
                LinearProgressIndicator(
                    progress = { category.percent.divide(BigDecimal(100)).toFloat().coerceIn(0f, 1f) },
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        }
        item {
            Text("Подписки", style = MaterialTheme.typography.titleLarge)
            Text("В месяц: ${data.subscriptions.monthlyTotal.money()} ₽")
            Text("В год: ${data.subscriptions.yearlyTotal.money()} ₽")
        }
    }
}

@Composable
private fun SummaryCard(title: String, value: String, modifier: Modifier = Modifier) {
    Card(modifier) { Column(Modifier.padding(12.dp)) { Text(title); Text(value, style = MaterialTheme.typography.titleLarge) } }
}

@Composable
private fun TimelineChart(points: List<TimelinePoint>) {
    val color = MaterialTheme.colorScheme.primary
    val max = points.maxOfOrNull { it.total } ?: BigDecimal.ZERO
    if (max.signum() == 0) {
        Text("За период нет динамики")
        return
    }
    Canvas(Modifier.fillMaxWidth().height(150.dp)) {
        val width = size.width / points.size.coerceAtLeast(1)
        points.forEachIndexed { index, point ->
            val height = size.height * point.total.divide(max, 6, RoundingMode.HALF_UP).toFloat()
            drawRect(color = color, topLeft = androidx.compose.ui.geometry.Offset(index * width + 2f, size.height - height), size = androidx.compose.ui.geometry.Size((width - 4f).coerceAtLeast(1f), height))
        }
    }
}

@Composable
private fun EmptyStatistics() {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text("За выбранный период расходов нет")
    }
}

@Composable
private fun ErrorStatistics(message: String, retry: () -> Unit) {
    Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.Center, horizontalAlignment = Alignment.CenterHorizontally) {
        Text(message, color = MaterialTheme.colorScheme.error)
        Button(onClick = retry) { Text("Повторить") }
    }
}

private fun BigDecimal.money(): String = setScale(2, RoundingMode.HALF_UP).toPlainString()
