package com.andrus.myexpenses.data.remote

import com.andrus.myexpenses.data.model.ApiErrorEnvelope
import com.google.gson.Gson
import retrofit2.Response

class ResponseMapper(
    private val gson: Gson,
) {
    fun <T : Any> requireBody(response: Response<T>): T {
        if (response.isSuccessful) {
            return response.body() ?: throw ApiException("EMPTY_RESPONSE", "Пустой ответ сервера", 502)
        }
        val apiError = runCatching {
            gson.fromJson(response.errorBody()?.string(), ApiErrorEnvelope::class.java)
        }.getOrNull()
        throw ApiException(
            code = apiError?.error?.code ?: "NETWORK_ERROR",
            message = apiError?.error?.message ?: "Не удалось выполнить запрос",
            status = response.code(),
        )
    }
}
