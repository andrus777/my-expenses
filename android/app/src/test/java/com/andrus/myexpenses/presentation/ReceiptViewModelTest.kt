package com.andrus.myexpenses.presentation

import com.andrus.myexpenses.MainDispatcherRule
import com.andrus.myexpenses.data.model.ReceiptJobDto
import com.andrus.myexpenses.domain.repository.ReceiptRepository
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class ReceiptViewModelTest {
    @get:Rule val dispatcherRule = MainDispatcherRule()

    @Test
    fun `blank receipt data produces understandable error without request`() {
        val viewModel = ReceiptViewModel(FakeReceiptRepository())

        viewModel.submit("  ")

        assertEquals("Введите данные QR-кода чека", (viewModel.state.value as ReceiptUiState.Error).message)
    }
}

private class FakeReceiptRepository : ReceiptRepository {
    override suspend fun submit(receiptData: String): ReceiptJobDto = error("must not be called")
    override suspend fun getJob(jobId: String): ReceiptJobDto = error("must not be called")
    override suspend fun finalize(receiptId: String, categoryId: String, operationId: String): String =
        error("must not be called")
}
