package com.andrus.myexpenses

import android.app.Application

class MyExpensesApplication : Application() {
    val container: AppContainer by lazy { AppContainer(this) }
}
