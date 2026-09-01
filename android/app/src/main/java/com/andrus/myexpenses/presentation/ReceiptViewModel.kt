package com.andrus.myexpenses.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.andrus.myexpenses.data.model.ReceiptJobDto
import com.andrus.myexpenses.domain.repository.ReceiptRepository
import java.util.UUID
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed interface ReceiptUiState {
    data object Input : ReceiptUiState
    data class Processing(val status: String) : ReceiptUiState
    data class Preview(val job: ReceiptJobDto) : ReceiptUiState
    data class Error(val message: String) : ReceiptUiState
    data object Finalized : ReceiptUiState
}

class ReceiptViewModel(private val repository: ReceiptRepository) : ViewModel() {
    private val mutableState = MutableStateFlow<ReceiptUiState>(ReceiptUiState.Input)
    val state = mutableState.asStateFlow()
    private var finalizeOperationId = UUID.randomUUID().toString()

    fun submit(data: String) {
        if (data.isBlank()) {
            mutableState.value = ReceiptUiState.Error("Введите данные QR-кода чека")
            return
        }
        viewModelScope.launch {
            runCatching {
                var job = repository.submit(data.trim())
                mutableState.value = ReceiptUiState.Processing(job.status)
                var polls = 0
                while (job.status in setOf("PENDING", "PROCESSING") && polls < 30) {
                    delay(2_000)
                    job = repository.getJob(job.job_id)
                    mutableState.value = ReceiptUiState.Processing(job.status)
                    polls++
                }
                when (job.status) {
                    "COMPLETED" -> mutableState.value = ReceiptUiState.Preview(job)
                    "FAILED" -> mutableState.value = ReceiptUiState.Error(job.error?.message ?: "Чек не распознан")
                    else -> mutableState.value = ReceiptUiState.Error("Обработка занимает больше обычного. Повторите позже")
                }
            }.onFailure { mutableState.value = ReceiptUiState.Error(it.message ?: "Нет связи с сервером") }
        }
    }

    fun finalize(categoryId: String) {
        val receiptId = (state.value as? ReceiptUiState.Preview)?.job?.receipt?.id ?: return
        if (categoryId.isBlank()) return
        viewModelScope.launch {
            runCatching { repository.finalize(receiptId, categoryId, finalizeOperationId) }
                .onSuccess { mutableState.value = ReceiptUiState.Finalized }
                .onFailure { mutableState.value = ReceiptUiState.Error(it.message ?: "Не удалось сохранить расход") }
        }
    }

    fun reset() {
        finalizeOperationId = UUID.randomUUID().toString()
        mutableState.value = ReceiptUiState.Input
    }

    class Factory(private val repository: ReceiptRepository) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T = ReceiptViewModel(repository) as T
    }
}
