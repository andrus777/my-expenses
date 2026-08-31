package com.andrus.myexpenses.tasks

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.Data
import androidx.work.ExistingWorkPolicy
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.andrus.myexpenses.R
import com.andrus.myexpenses.domain.model.Subscription
import com.andrus.myexpenses.domain.repository.SubscriptionNotificationScheduler
import java.time.Duration
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.util.concurrent.TimeUnit

class SubscriptionNotificationWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        val name = inputData.getString(NAME) ?: return Result.failure()
        val days = inputData.getInt(DAYS, 1)
        val manager = applicationContext.getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(NotificationChannel(CHANNEL, "Платежи по подпискам", NotificationManager.IMPORTANCE_DEFAULT))
        val notification = NotificationCompat.Builder(applicationContext, CHANNEL)
            .setSmallIcon(R.drawable.ic_launcher)
            .setContentTitle("Скоро платёж")
            .setContentText("$name: оплата через $days дн.")
            .setAutoCancel(true)
            .build()
        manager.notify("$name-$days".hashCode(), notification)
        return Result.success()
    }

    companion object {
        const val NAME = "name"
        const val DAYS = "days"
        const val CHANNEL = "subscription_payments"
    }
}

class WorkManagerSubscriptionNotificationScheduler(private val context: Context) : SubscriptionNotificationScheduler {
    override fun schedule(subscriptions: List<Subscription>) {
        val manager = WorkManager.getInstance(context)
        manager.cancelAllWorkByTag(REMINDER_TAG)
        subscriptions.filter { it.isActive }.forEach { subscription ->
            listOf(7, 3, 1).forEach { days ->
                val delay = notificationDelayMillis(subscription.nextPaymentDate, days)
                val uniqueName = "subscription-${subscription.id}-$days"
                if (delay != null) {
                    val work = OneTimeWorkRequestBuilder<SubscriptionNotificationWorker>()
                        .addTag(REMINDER_TAG)
                        .setInitialDelay(delay, TimeUnit.MILLISECONDS)
                        .setInputData(Data.Builder().putString(SubscriptionNotificationWorker.NAME, subscription.name).putInt(SubscriptionNotificationWorker.DAYS, days).build())
                        .build()
                    manager.enqueueUniqueWork(uniqueName, ExistingWorkPolicy.REPLACE, work)
                } else {
                    manager.cancelUniqueWork(uniqueName)
                }
            }
        }
    }

    private companion object {
        const val REMINDER_TAG = "subscription-reminder"
    }
}

internal fun notificationDelayMillis(
    date: String,
    daysBefore: Int,
    now: Instant = Instant.now(),
    zoneId: ZoneId = ZoneId.systemDefault(),
): Long? {
    val trigger = LocalDate.parse(date).minusDays(daysBefore.toLong()).atTime(9, 0).atZone(zoneId).toInstant()
    return Duration.between(now, trigger).toMillis().takeIf { it > 0 }
}
