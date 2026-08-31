package com.andrus.myexpenses.tasks

import android.content.Context
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.andrus.myexpenses.MyExpensesApplication
import com.andrus.myexpenses.domain.repository.ExpenseRepository
import com.andrus.myexpenses.domain.repository.SyncOutcome
import com.andrus.myexpenses.domain.repository.SyncScheduler
import java.time.Duration

class ExpenseSyncWorker(
    appContext: Context,
    params: WorkerParameters,
) : CoroutineWorker(appContext, params) {
    override suspend fun doWork(): Result =
        runSync((applicationContext as MyExpensesApplication).container.expenseRepository)

    companion object {
        const val UNIQUE_WORK_NAME = "expense-sync"

        internal suspend fun runSync(repository: ExpenseRepository): Result =
            when (repository.sync()) {
                SyncOutcome.SUCCESS -> Result.success()
                SyncOutcome.RETRY -> Result.retry()
            }
    }
}

class WorkManagerSyncScheduler(context: Context) : SyncScheduler {
    private val workManager = WorkManager.getInstance(context)

    override fun schedule() {
        val request = OneTimeWorkRequestBuilder<ExpenseSyncWorker>()
            .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
            .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, Duration.ofSeconds(10))
            .build()
        workManager.enqueueUniqueWork(
            ExpenseSyncWorker.UNIQUE_WORK_NAME,
            ExistingWorkPolicy.APPEND_OR_REPLACE,
            request,
        )
    }
}
