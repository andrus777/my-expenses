package com.andrus.myexpenses

import android.os.Bundle
import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.andrus.myexpenses.ui.MyExpensesApp
import com.andrus.myexpenses.ui.theme.MyExpensesTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (android.os.Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1001)
        }
        val container = (application as MyExpensesApplication).container
        setContent {
            MyExpensesTheme {
                MyExpensesApp(
                    container.authRepository,
                    container.expenseRepository,
                    container.subscriptionRepository,
                    container.receiptRepository,
                    container.statisticsRepository,
                    container.budgetRepository,
                )
            }
        }
    }
}
