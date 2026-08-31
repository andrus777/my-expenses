package com.andrus.myexpenses.data.local

import androidx.room.Entity
import androidx.room.Index
import com.andrus.myexpenses.domain.model.Category

@Entity(
    tableName = "categories",
    primaryKeys = ["ownerUserId", "id"],
    indices = [Index(value = ["ownerUserId"])],
)
data class CategoryEntity(
    val ownerUserId: String,
    val id: String,
    val name: String,
    val isSystem: Boolean,
) {
    fun toDomain() = Category(id, name)
}
