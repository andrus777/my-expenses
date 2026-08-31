package com.andrus.myexpenses.data.remote

import com.andrus.myexpenses.data.model.UserDto

interface UserRemoteDataSource {
    suspend fun me(): UserDto
}

class RetrofitUserRemoteDataSource(
    private val api: UserApi,
    private val responses: ResponseMapper,
) : UserRemoteDataSource {
    override suspend fun me(): UserDto = responses.requireBody(api.me()).user
}
