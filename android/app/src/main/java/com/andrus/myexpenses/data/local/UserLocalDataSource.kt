package com.andrus.myexpenses.data.local

import com.andrus.myexpenses.domain.model.User
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

interface UserLocalDataSource {
    val user: Flow<User?>

    suspend fun save(user: User)

    suspend fun clear()
}

class RoomUserLocalDataSource(
    private val dao: UserDao,
) : UserLocalDataSource {
    override val user: Flow<User?> = dao.observe().map { it?.toDomain() }

    override suspend fun save(user: User) = dao.save(UserEntity.fromDomain(user))

    override suspend fun clear() = dao.clear()
}
