-- AI Patrol/Chase State Machine
local AIPatrol = {
    Properties = {
        PatrolSpeed = { default = 3.0 },
        ChaseSpeed = { default = 6.0 },
        DetectionRange = { default = 20.0 },
        LoseRange = { default = 30.0 },
        PatrolWaitTime = { default = 2.0 },
    },
}

function AIPatrol:OnActivate()
    self.state = "patrol"
    self.waitTimer = 0
    self.isWaiting = false
    self.targetEntityId = nil
    self.tickHandler = TickBus.Connect(self, 0)
end

function AIPatrol:OnDeactivate()
    self.tickHandler:Disconnect()
end

function AIPatrol:OnTick(deltaTime, timePoint)
    local myPos = TransformBus.Event.GetWorldTranslation(self.entityId)
    if self.state == "patrol" then
        if self:DetectPlayer(myPos) then
            self.state = "chase"
        end
    elseif self.state == "chase" then
        if not self:DetectPlayer(myPos) then
            self.state = "patrol"
        else
            self:ChaseTick(deltaTime, myPos)
        end
    end
end

function AIPatrol:DetectPlayer(myPos)
    local allEntities = TagGlobalRequestBus.Connect(self, "Player")
    if allEntities then
        for _, playerId in ipairs(allEntities) do
            if playerId and playerId:IsValid() then
                local playerPos = TransformBus.Event.GetWorldTranslation(playerId)
                local dist = (playerPos - myPos):GetLength()
                if dist < self.Properties.DetectionRange then
                    self.targetEntityId = playerId
                    return true
                end
            end
        end
    end
    return false
end

function AIPatrol:ChaseTick(deltaTime, myPos)
    if not self.targetEntityId or not self.targetEntityId:IsValid() then return end
    local targetPos = TransformBus.Event.GetWorldTranslation(self.targetEntityId)
    local direction = (targetPos - myPos):GetNormalized()
    local newPos = myPos + direction * self.Properties.ChaseSpeed * deltaTime
    TransformBus.Event.SetWorldTranslation(self.entityId, newPos)
end
