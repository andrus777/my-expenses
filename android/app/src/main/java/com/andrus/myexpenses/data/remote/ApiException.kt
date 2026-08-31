package com.andrus.myexpenses.data.remote

class ApiException(
    val code: String,
    override val message: String,
    val status: Int,
) : Exception(message)
