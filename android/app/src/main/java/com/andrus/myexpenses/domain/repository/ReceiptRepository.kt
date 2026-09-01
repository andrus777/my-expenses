package com.andrus.myexpenses.domain.repository

import com.andrus.myexpenses.data.model.ReceiptJobDto

interface ReceiptRepository {
    suspend fun submit(receiptData: String): ReceiptJobDto
    suspend fun getJob(jobId: String): ReceiptJobDto
    suspend fun finalize(receiptId: String, categoryId: String, operationId: String): String
}
