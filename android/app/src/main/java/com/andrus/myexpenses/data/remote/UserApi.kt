package com.andrus.myexpenses.data.remote

import com.andrus.myexpenses.data.model.UserResponse
import retrofit2.Response
import retrofit2.http.GET

interface UserApi {
    @GET("users/me")
    suspend fun me(): Response<UserResponse>
}
