package com.andrus.myexpenses.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.andrus.myexpenses.domain.model.User

@Entity(tableName = "current_user")
data class UserEntity(
    @PrimaryKey val id: String,
    val email: String,
    val createdAt: String,
    val updatedAt: String,
) {
    fun toDomain() = User(id, email, createdAt, updatedAt)

    companion object {
        fun fromDomain(user: User) = UserEntity(user.id, user.email, user.createdAt, user.updatedAt)
    }
}
