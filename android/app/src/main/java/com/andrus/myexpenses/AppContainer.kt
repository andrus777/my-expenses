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
import com.andrus.myexpenses.data.remote.ResponseMapper
import com.andrus.myexpenses.data.remote.RetrofitAuthRemoteDataSource
import com.andrus.myexpenses.data.remote.RetrofitUserRemoteDataSource
import com.andrus.myexpenses.data.remote.TokenRefreshAuthenticator
import com.andrus.myexpenses.data.remote.UserApi
import com.andrus.myexpenses.data.repository.DefaultAuthRepository
import com.andrus.myexpenses.domain.repository.AuthRepository
import com.google.gson.Gson
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

private val Context.authDataStore by preferencesDataStore(name = "secure_auth")

class AppContainer(context: Context) {
    private val gson = Gson()
    private val authLocal =
        EncryptedAuthLocalDataSource(context.authDataStore, AndroidKeyStoreTokenCipher())
    private val database =
        Room.databaseBuilder(context, AppDatabase::class.java, "my-expenses.db").build()
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

    private fun retrofit(client: OkHttpClient): Retrofit =
        Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create(gson))
            .build()
}
