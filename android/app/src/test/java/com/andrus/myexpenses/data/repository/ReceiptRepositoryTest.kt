package com.andrus.myexpenses.data.repository

import com.andrus.myexpenses.data.model.ReceiptJobCreated
import com.andrus.myexpenses.data.model.ReceiptJobDto
import com.andrus.myexpenses.data.remote.ReceiptApi
import com.andrus.myexpenses.data.remote.ResponseMapper
import com.google.gson.Gson
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Test
import retrofit2.Response

class ReceiptRepositoryTest {
    @Test
    fun `submit talks only to backend and returns normalized job`() = runTest {
        val api = mockk<ReceiptApi>()
        coEvery { api.create(any()) } returns Response.success(ReceiptJobCreated("job-id", "PENDING"))
        coEvery { api.job("job-id") } returns Response.success(
            ReceiptJobDto("job-id", "PROCESSING", 1, null, null),
        )
        val repository = DefaultReceiptRepository(api, ResponseMapper(Gson()))

        val job = repository.submit("qr-data")

        assertEquals("job-id", job.job_id)
        assertEquals("PROCESSING", job.status)
    }
}
