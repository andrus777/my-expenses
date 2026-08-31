package com.andrus.myexpenses.domain.model

data class AuthTokens(
    val accessToken: String,
    val refreshToken: String,
)
