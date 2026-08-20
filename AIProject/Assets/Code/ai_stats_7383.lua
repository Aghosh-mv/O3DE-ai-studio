-- Character Stats System
local StatsSystem = { Properties = {
    MaxHealth = { default = 100 }, MaxStamina = { default = 100 },
    Strength = { default = 10 }, Defense = { default = 5 }, Speed = { default = 8 },
} }
function StatsSystem:OnActivate()
    self.health = self.Properties.MaxHealth
    self.stamina = self.Properties.MaxStamina
    self.level = 1
    self.xp = 0
end
function StatsSystem:OnDeactivate() end
function StatsSystem:TakeDamage(amount)
    local reduced = math.max(1, amount - self.Properties.Defense)
    self.health = math.max(0, self.health - reduced)
    if self.health <= 0 then Debug.Log("Entity died!") end
end
function StatsSystem:Heal(amount) self.health = math.min(self.Properties.MaxHealth, self.health + amount) end
function StatsSystem:AddXP(amount)
    self.xp = self.xp + amount
    if self.xp >= self.level * 100 then
        self.level = self.level + 1
        self.xp = 0
        Debug.Log("Level up! Now level " .. self.level)
    end
end
