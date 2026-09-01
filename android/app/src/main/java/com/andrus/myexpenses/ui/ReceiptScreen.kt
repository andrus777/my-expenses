package com.andrus.myexpenses.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.andrus.myexpenses.domain.model.Category
import com.andrus.myexpenses.presentation.ReceiptUiState
import com.andrus.myexpenses.presentation.ReceiptViewModel

@Composable
fun ReceiptScreen(viewModel: ReceiptViewModel, categories: List<Category>, onDone: () -> Unit) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var receiptData by remember { mutableStateOf("") }
    var categoryId by remember { mutableStateOf(categories.firstOrNull()?.id.orEmpty()) }
    Column(
        Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Добавить по чеку")
        when (val value = state) {
            ReceiptUiState.Input -> {
                OutlinedTextField(
                    receiptData,
                    { receiptData = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Данные QR-кода") },
                )
                Button(onClick = { viewModel.submit(receiptData) }) { Text("Распознать") }
            }
            is ReceiptUiState.Processing -> Row(verticalAlignment = Alignment.CenterVertically) {
                CircularProgressIndicator()
                Text(" Обработка: ${value.status}")
            }
            is ReceiptUiState.Preview -> {
                val receipt = value.job.receipt ?: return@Column
                Text("${receipt.merchant} · ${receipt.total} ${receipt.currency}")
                Text(receipt.purchase_date)
                receipt.items.forEach { Text("${it.name}: ${it.quantity} × ${it.price} = ${it.total}") }
                Text("Категория")
                categories.forEach { category ->
                    TextButton(onClick = { categoryId = category.id }) {
                        Text(if (categoryId == category.id) "✓ ${category.name}" else category.name)
                    }
                }
                Button(onClick = { viewModel.finalize(categoryId) }, enabled = categoryId.isNotBlank()) {
                    Text("Подтвердить и создать расход")
                }
            }
            is ReceiptUiState.Error -> {
                Text(value.message)
                Button(onClick = viewModel::reset) { Text("Попробовать снова") }
            }
            ReceiptUiState.Finalized -> {
                Text("Расход создан")
                Button(onClick = onDone) { Text("Готово") }
            }
        }
        TextButton(onClick = onDone) { Text("Назад") }
    }
}
