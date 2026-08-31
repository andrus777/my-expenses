package com.andrus.myexpenses.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.andrus.myexpenses.domain.model.Subscription
import com.andrus.myexpenses.presentation.SubscriptionViewModel
import java.math.BigDecimal
import java.time.LocalDate

@Composable
fun SubscriptionScreen(viewModel: SubscriptionViewModel) {
    val state by viewModel.state.collectAsState()
    var editing by remember { mutableStateOf<Subscription?>(null) }
    var creating by remember { mutableStateOf(false) }
    var historyFor by remember { mutableStateOf<String?>(null) }
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Подписки", style = MaterialTheme.typography.headlineMedium)
            Button(onClick = { creating = true; editing = null }) { Text("Добавить") }
        }
        state.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        if (state.loading) LinearProgressIndicator(Modifier.fillMaxWidth())
        Text("Ближайшие платежи", style = MaterialTheme.typography.titleMedium)
        LazyColumn {
            items(state.subscriptions, key = { it.id }) { subscription ->
                Card(Modifier.fillMaxWidth().padding(vertical = 4.dp).clickable { editing = subscription; creating = true }) {
                    Column(Modifier.padding(12.dp)) {
                        Text(subscription.name, style = MaterialTheme.typography.titleMedium)
                        Text("${subscription.amountMinor.money()} ${subscription.currency} · ${subscription.nextPaymentDate}")
                        Row {
                            Button(onClick = { viewModel.pay(subscription.id) }) { Text("Оплачено") }
                            TextButton(onClick = { historyFor = subscription.id; viewModel.history(subscription.id) }) { Text("История") }
                        }
                    }
                }
            }
        }
        if (historyFor != null) {
            Text("История оплат", style = MaterialTheme.typography.titleMedium)
            state.payments.filter { it.subscriptionId == historyFor }.forEach {
                Text("${it.paymentDate}: ${it.amountMinor.money()} RUB")
            }
            if (state.payments.none { it.subscriptionId == historyFor }) Text("Оплат пока нет")
        }
    }
    if (creating) SubscriptionForm(editing, state.categories, viewModel, { creating = false }, { creating = false })
}

@Composable
private fun SubscriptionForm(item: Subscription?, categories: List<com.andrus.myexpenses.domain.model.Category>, viewModel: SubscriptionViewModel, onDone: () -> Unit, onDismiss: () -> Unit) {
    var name by remember(item?.id) { mutableStateOf(item?.name.orEmpty()) }
    var amount by remember(item?.id) { mutableStateOf(item?.amountMinor?.money().orEmpty()) }
    var category by remember(item?.id) { mutableStateOf(item?.categoryId ?: categories.firstOrNull()?.id.orEmpty()) }
    var frequency by remember(item?.id) { mutableStateOf(item?.frequency ?: "MONTHLY") }
    var interval by remember(item?.id) { mutableStateOf(item?.customIntervalDays?.toString().orEmpty()) }
    var date by remember(item?.id) { mutableStateOf(item?.nextPaymentDate ?: LocalDate.now().plusMonths(1).toString()) }
    var error by remember { mutableStateOf<String?>(null) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (item == null) "Новая подписка" else "Редактировать подписку") },
        text = {
            Column {
                OutlinedTextField(name, { name = it }, label = { Text("Название") })
                OutlinedTextField(amount, { amount = it }, label = { Text("Сумма") })
                OutlinedTextField(date, { date = it }, label = { Text("Следующий платёж YYYY-MM-DD") })
                Text("Категория")
                categories.forEach { value -> TextButton(onClick = { category = value.id }) { Text(if (category == value.id) "✓ ${value.name}" else value.name) } }
                Text("Периодичность")
                listOf("WEEKLY", "MONTHLY", "QUARTERLY", "HALF_YEAR", "YEARLY", "CUSTOM").forEach { value ->
                    TextButton(onClick = { frequency = value }) { Text(if (frequency == value) "✓ $value" else value) }
                }
                if (frequency == "CUSTOM") OutlinedTextField(interval, { interval = it }, label = { Text("Интервал, дней") })
                error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
                if (item != null) TextButton(onClick = { viewModel.delete(item.id); onDone() }) { Text("Удалить") }
            }
        },
        confirmButton = { TextButton(onClick = { error = viewModel.save(item?.id, name, amount, category, frequency, interval, date); if (error == null) onDone() }) { Text("Сохранить") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Отмена") } },
    )
}

private fun Long.money() = BigDecimal.valueOf(this, 2).toPlainString()
