package com.andrus.myexpenses

import android.content.Context
import androidx.datastore.preferences.preferencesDataStore
import androidx.room.Room
import com.andrus.myexpenses.data.local.AndroidKeyStoreTokenCipher
import com.andrus.myexpenses.data.local.AppDatabase
import com.andrus.myexpenses.data.local.EncryptedAuthLocalDataSource
import com.andrus.myexpenses.data.local.RoomUserLocalDataSource
import com.andrus.myexpenses.data.remote.AccessTokenInterceptor
import com.andrus.myexpenses.data.remote.AuthApi
import com.andrus.myexpenses.data.remote.BudgetApi
import com.andrus.myexpenses.data.remote.ExpenseApi
import com.andrus.myexpenses.data.remote.RetrofitExpenseRemoteDataSource
import com.andrus.myexpenses.data.remote.ReceiptApi
import com.andrus.myexpenses.data.remote.ResponseMapper
import com.andrus.myexpenses.data.remote.RetrofitAuthRemoteDataSource
import com.andrus.myexpenses.data.remote.RetrofitUserRemoteDataSource
import com.andrus.myexpenses.data.remote.TokenRefreshAuthenticator
import com.andrus.myexpenses.data.remote.UserApi
import com.andrus.myexpenses.data.remote.SubscriptionApi
import com.andrus.myexpenses.data.remote.StatisticsApi
import com.andrus.myexpenses.data.repository.DefaultAuthRepository
import com.andrus.myexpenses.data.repository.DefaultBudgetRepository
import com.andrus.myexpenses.data.repository.DefaultExpenseRepository
import com.andrus.myexpenses.data.repository.DefaultReceiptRepository
import com.andrus.myexpenses.data.repository.DefaultSubscriptionRepository
import com.andrus.myexpenses.data.repository.DefaultStatisticsRepository
import com.andrus.myexpenses.domain.repository.AuthRepository
import com.andrus.myexpenses.domain.repository.BudgetRepository
import com.andrus.myexpenses.domain.repository.ExpenseRepository
import com.andrus.myexpenses.domain.repository.ReceiptRepository
import com.andrus.myexpenses.domain.repository.SubscriptionRepository
import com.andrus.myexpenses.domain.repository.StatisticsRepository
import com.andrus.myexpenses.tasks.WorkManagerSubscriptionNotificationScheduler
import com.andrus.myexpenses.tasks.WorkManagerSyncScheduler
import com.google.gson.Gson
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import kotlinx.coroutines.flow.map

private val Context.authDataStore by preferencesDataStore(name = "secure_auth")

class AppContainer(context: Context) {
    private val gson = Gson()
    private val authLocal =
        EncryptedAuthLocalDataSource(context.authDataStore, AndroidKeyStoreTokenCipher())
    private val database =
        Room.databaseBuilder(context, AppDatabase::class.java, "my-expenses.db")
            .addMigrations(AppDatabase.MIGRATION_1_2)
            .build()
    private val userLocal = RoomUserLocalDataSource(database.userDao())
    private val logging =
        HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BASIC else {
                HttpLoggingInterceptor.Level.NONE
            }
        }
    private val publicClient = OkHttpClient.Builder().addInterceptor(logging).build()
    private val publicRetrofit = retrofit(publicClient)
    private val authApi = publicRetrofit.create(AuthApi::class.java)
    private val authenticatedClient =
        OkHttpClient.Builder()
            .addInterceptor(AccessTokenInterceptor(authLocal))
            .addInterceptor(logging)
            .authenticator(TokenRefreshAuthenticator(authLocal, authApi))
            .build()
    private val authenticatedRetrofit = retrofit(authenticatedClient)

    val authRepository: AuthRepository =
        DefaultAuthRepository(
            authRemote = RetrofitAuthRemoteDataSource(authApi, ResponseMapper(gson)),
            userRemote = RetrofitUserRemoteDataSource(
                authenticatedRetrofit.create(UserApi::class.java),
                ResponseMapper(gson),
            ),
            authLocal = authLocal,
            userLocal = userLocal,
        )

    val expenseRepository: ExpenseRepository =
        DefaultExpenseRepository(
            expenseDao = database.expenseDao(),
            categoryDao = database.categoryDao(),
            remote = RetrofitExpenseRemoteDataSource(
                authenticatedRetrofit.create(ExpenseApi::class.java),
                ResponseMapper(gson),
            ),
            currentUserId = userLocal.user.map { it?.id },
            scheduler = WorkManagerSyncScheduler(context),
        )

    val subscriptionRepository: SubscriptionRepository =
        DefaultSubscriptionRepository(
            authenticatedRetrofit.create(SubscriptionApi::class.java),
            ResponseMapper(gson),
            WorkManagerSubscriptionNotificationScheduler(context),
        )

    val receiptRepository: ReceiptRepository =
        DefaultReceiptRepository(
            authenticatedRetrofit.create(ReceiptApi::class.java),
            ResponseMapper(gson),
        )

    val statisticsRepository: StatisticsRepository =
        DefaultStatisticsRepository(
            authenticatedRetrofit.create(StatisticsApi::class.java),
            ResponseMapper(gson),
        )

    val budgetRepository: BudgetRepository =
        DefaultBudgetRepository(
            authenticatedRetrofit.create(BudgetApi::class.java),
            ResponseMapper(gson),
        )

    private fun retrofit(client: OkHttpClient): Retrofit =
        Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create(gson))
            .build()
}
