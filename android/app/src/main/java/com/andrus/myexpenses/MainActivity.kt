package com.andrus.myexpenses

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.andrus.myexpenses.ui.MyExpensesApp
import com.andrus.myexpenses.ui.theme.MyExpensesTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val container = (application as MyExpensesApplication).container
        setContent {
            MyExpensesTheme {
                MyExpensesApp(container.authRepository)
            }
        }
    }
}
