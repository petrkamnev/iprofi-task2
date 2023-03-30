from aiohttp import web
import json
import random
import copy

class ParticipantManager:
    def __init__(self):
        self.m_participants = []
        self.m_currendMaxParticipantId = 1
        self.m_groupIds = []
        self.m_recipients = dict()

    def find_participant(self, participantId = None):
        indexOfParticipant = -1
        for index, participant in enumerate(self.m_participants):
            if participant['id'] == participantId:
                indexOfParticipant = index
                break
        return indexOfParticipant

    def check_in_group(self, groupId, participantId):
        return self.m_groupIds[self.find_participant(participantId)] == groupId

    def generate_id(self):
        id = self.m_currendMaxParticipantId
        self.m_currendMaxParticipantId += 1
        return id

    def create_participant(self, groupID=None, name=None, wish=None):
        if name == None:
            raise Exception()
        result = dict()
        result['id'] = self.generate_id()
        result['name'] = str(name)
        if wish is not None:
            result['wish'] = str(wish)
        self.m_participants.append(result)
        self.m_groupIds.append(groupID)
        return result['id']

    def delete_participant(self, participantId=None):
        indexOfParticipant = self.find_participant(participantId)
        if indexOfParticipant == -1:
            raise Exception
        self.m_participants.pop(indexOfParticipant)
        self.m_groupIds.pop(indexOfParticipant)
        if participantId in self.m_recipients.keys():
            self.m_recipients.pop(participantId)
        return False

    def delete_by_group(self, groupId=None):
        for index in reversed(range(len(self.m_participants))):
            if self.m_groupIds[index] == groupId:
                if self.m_participants[index]['id'] in self.m_recipients.keys():
                    self.m_recipients.pop(self.m_participants[index]['id'])
                self.m_participants.pop(index)
                self.m_groupIds.pop(index)

    def do_toss(self, groupId=None):
        listOfIndexes = []
        for index in range(len(self.m_participants)):
            if self.m_groupIds[index] == groupId:
                listOfIndexes.append(index)
        if len(listOfIndexes) < 3:
            return -1
        possibleRecipients = listOfIndexes[:]
        currentFriend = 0
        while not (len(possibleRecipients) == 0):
            generatedIndex = random.randint(0, len(possibleRecipients) - 1)
            if possibleRecipients[generatedIndex] != currentFriend:
                self.m_recipients[self.m_participants[currentFriend]['id']] = self.m_participants[possibleRecipients[generatedIndex]]
                possibleRecipients.pop(generatedIndex)
                currentFriend += 1
        result = []
        for index in listOfIndexes:
            item = copy.copy(self.m_participants[index])
            item['recipient'] = self.m_recipients[item['id']]
            result.append(item)
        return result

    def get_recipient(self, id=None):
        result = self.m_recipients[id]
        return result

    def get_group(self, id=None):
        listOfIndexes = []
        for index in range(len(self.m_participants)):
            if self.m_groupIds[index] == id:
                listOfIndexes.append(index)
        result = []
        for index in listOfIndexes:
            item = copy.copy(self.m_participants[index])
            if self.m_participants[index]['id'] in self.m_recipients.keys():
                item['recipient'] = self.m_recipients[item['id']]
            result.append(item)
        return result

class GroupManager:

    def __init__(self):
        self.m_groups = []
        self.m_currendMaxGroupId = 1
        self.m_particimantsManager = ParticipantManager()

    def generate_id(self):
        id = self.m_currendMaxGroupId
        self.m_currendMaxGroupId += 1
        return id

    def find_group(self, groupID = None):
        indexOfGroup = -1
        for index, group in enumerate(self.m_groups):
            if group['id'] == groupID:
                indexOfGroup = index
                break
        return indexOfGroup
    def add_group(self, name=None, description=None):
        if name == None:
            raise Exception()
        result = dict()
        result['id'] = self.generate_id()
        result['name'] = str(name)
        if description is not None:
            result['description'] = str(description)
        self.m_groups.append(result)
        return result['id']

    def get_groups(self):
        return self.m_groups

    def edit_group(self, id=None, name=None, description=None):
        indexOfGroup = self.find_group(id)
        if indexOfGroup == -1:
            raise Exception()
        if name == None:
            raise Exception()
        result = dict()
        result['id'] = id
        result['name'] = str(name)
        if description is not None:
            result['description'] = str(description)
        self.m_groups[indexOfGroup] = result
        return False

    def delete_group(self, id):
        indexOfGroup = self.find_group(id)
        if indexOfGroup == -1:
            return web.Response(status=404)
        self.m_particimantsManager.delete_by_group(id)
        self.m_groups.pop(indexOfGroup)
        return False

    def add_participant(self, groupID=None, name=None, wish=None):
        indexOfGroup = self.find_group(groupID)
        if indexOfGroup == -1:
            raise Exception()
        id = self.m_particimantsManager.create_participant(groupID, name, wish)
        return id

    def delete_participant(self, groupId=None, participantId=None):
        if not self.m_particimantsManager.check_in_group(groupId, participantId):
            raise Exception()
        self.m_particimantsManager.delete_participant(participantId)
        return False

    def do_toss(self, id):
        result = self.m_particimantsManager.do_toss(id)
        return result

    def get_recipient(self, groupId=None, participantId=None):
        if not self.m_particimantsManager.check_in_group(groupId, participantId):
            raise Exception()
        result = self.m_particimantsManager.get_recipient(participantId)
        return result

    def get_group(self, id=None):
        indexOfGroup = self.find_group(id)
        if indexOfGroup == -1:
            return web.Response(status=404)
        result = self.m_particimantsManager.get_group(id)
        return result

#--------------------------------------#

class Handler:

    def __init__(self):
        self.m_groupManager = GroupManager()
        pass

    async def add_group(self, request):
        try:
            data = await request.json()
            name = data['name']
            description = None
            if 'description' in data.keys():
                description = str(data['description'])
            id = self.m_groupManager.add_group(name, description)
            return web.Response(text=str(id), status=200)
        except Exception:
            return web.Response(status=404)

    async def get_groups(self, request):
        try:
            return web.json_response(self.m_groupManager.get_groups(), status=200)
        except Exception:
            return web.Response(status=404)

    async def edit_group(self, request):
        try:
            id = int(request.match_info['id'])
            data = await request.json()
            if data == None:
                return web.Response(status=404)

            name = data['name']
            description = None
            if 'description' in data.keys():
                description = str(data['description'])
            self.m_groupManager.edit_group(id, name, description)
            return web.Response(status=200)
        except Exception:
            return web.Response(status=404)

    async def delete_group(self, request):
        try:
            id = int(request.match_info['id'])
            self.m_groupManager.delete_group(id)
            return web.Response(status=200)
        except Exception:
            return web.Response(status=404)

    async def add_participant(self, request):
        try:
            id = int(request.match_info['id'])
            data = await request.json()
            name = data['name']
            wish = None
            if 'wish' in data.keys():
                wish = str(data['wish'])
            participantID = self.m_groupManager.add_participant(id, name, wish)
            return web.Response(text=str(participantID), status=200)
        except Exception:
            return web.Response(status=404)

    async def delete_participant(self, request):
        try:
            groupId = int(request.match_info['groupId'])
            participantId = int(request.match_info['participantId'])

            return web.Response(text=str(participantId), status=200)
        except Exception:
            return web.Response(status=404)

    async def do_toss(self, request):
        try:
            id = int(request.match_info['id'])
            result = self.m_groupManager.do_toss(id)
            if result == -1:
                return web.Response(status=409)
            return web.json_response(result, status=200)
        except Exception:
            return web.Response(status=404)

    async def get_recipient(self, request):
        try:
            groupId = int(request.match_info['groupId'])
            participantId = int(request.match_info['participantId'])
            result = self.m_groupManager.get_recipient(groupId, participantId)
            return web.json_response(result, status=200)
        except Exception:
            return web.Response(status=404)

    async def get_group(self, request):
        try:
            id = int(request.match_info['id'])
            result = self.m_groupManager.get_group(id)
            return web.json_response(result, status=200)
        except Exception:
            return web.Response(status=404)

routes = web.RouteTableDef()

app = web.Application()
handler = Handler()
app.add_routes([web.post('/group', handler.add_group),
                web.put('/group/{id}', handler.edit_group),
                web.delete('/group/{id}', handler.delete_group),
                web.get('/group/{id}', handler.get_group),
                web.post('/group/{id}/participant', handler.add_participant),
                web.delete('/group/{groupId}/participant/{participantId}', handler.delete_participant),
                web.post('/group/{id}/toss', handler.do_toss),
                web.get('/group/{groupId}/participant/{participantId}/recipient', handler.get_recipient),
                web.get('/groups', handler.get_groups)])

async def main():
    return app

if __name__ == '__main__':
    web.run_app(main())
