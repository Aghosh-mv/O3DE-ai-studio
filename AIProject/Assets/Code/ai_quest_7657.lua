-- Quest System
local QuestSystem = { Properties = { MaxQuests = { default = 10 } } }
function QuestSystem:OnActivate()
    self.quests = {}
    self.activeQuests = {}
end
function QuestSystem:OnDeactivate() end
function QuestSystem:AcceptQuest(quest)
    if #self.activeQuests >= self.Properties.MaxQuests then return false end
    quest.status = "active"
    quest.progress = 0
    table.insert(self.activeQuests, quest)
    return true
end
function QuestSystem:CompleteQuest(questId)
    for i, q in ipairs(self.activeQuests) do
        if q.id == questId then
            q.status = "completed"
            table.remove(self.activeQuests, i)
            return true
        end
    end
    return false
end
function QuestSystem:GetActiveQuests() return self.activeQuests end
