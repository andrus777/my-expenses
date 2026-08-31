package com.andrus.myexpenses.tasks

import androidx.work.ListenableWorker
import com.andrus.myexpenses.domain.repository.ExpenseRepository
import com.andrus.myexpenses.domain.repository.SyncOutcome
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Test

class ExpenseSyncWorkerTest {
    @Test
    fun `transient sync outcome requests WorkManager retry`() = runTest {
        val repository = mockk<ExpenseRepository>()
        coEvery { repository.sync() } returns SyncOutcome.RETRY

        val result = ExpenseSyncWorker.runSync(repository)

        assertEquals(ListenableWorker.Result.retry()::class, result::class)
    }

    @Test
    fun `successful sync completes work`() = runTest {
        val repository = mockk<ExpenseRepository>()
        coEvery { repository.sync() } returns SyncOutcome.SUCCESS

        val result = ExpenseSyncWorker.runSync(repository)

        assertEquals(ListenableWorker.Result.success()::class, result::class)
    }
}
