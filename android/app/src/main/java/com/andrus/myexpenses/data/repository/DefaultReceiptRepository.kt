package com.andrus.myexpenses.data.repository

import com.andrus.myexpenses.data.model.ReceiptFinalizeRequest
import com.andrus.myexpenses.data.model.ReceiptJobDto
import com.andrus.myexpenses.data.model.ReceiptJobRequest
import com.andrus.myexpenses.data.remote.ReceiptApi
import com.andrus.myexpenses.data.remote.ResponseMapper
import com.andrus.myexpenses.domain.repository.ReceiptRepository

class DefaultReceiptRepository(
    private val api: ReceiptApi,
    private val responses: ResponseMapper,
) : ReceiptRepository {
    override suspend fun submit(receiptData: String): ReceiptJobDto {
        val created = responses.requireBody(api.create(ReceiptJobRequest(receiptData)))
        return getJob(created.job_id)
    }

    override suspend fun getJob(jobId: String): ReceiptJobDto = responses.requireBody(api.job(jobId))

    override suspend fun finalize(receiptId: String, categoryId: String, operationId: String): String =
        responses.requireBody(
            api.finalize(receiptId, ReceiptFinalizeRequest(categoryId, operationId)),
        ).expense.id
}
