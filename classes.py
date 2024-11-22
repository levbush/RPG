from random import randint
from time import sleep
from dataclasses import dataclass

@dataclass
class Item:
    name: str
    description: str = ''
    requirements: dict = None
    quality: str = 'Common'
    trigger: 'Quest' = None
    def __str__(self):
        return f'{self.name}: {self.description}'
    def trigger_quest(self, player: 'Character'):
        """Trigger the quest for the player."""
        if self.trigger:
            player.complete_quest(self.trigger)

@dataclass
class Artifact(Item):
    name: str
    description: str = ''
    traits: dict=None

@dataclass
class Weapon(Item):
    character_class: str = 'Warrior'
    damage: float = 10.0
    durability: float = 100.0
    quality: str = 'Common'
    weapon_type: str = 'Weapon'
    def __str__(self):
        return f'Weapon {self.name} with damage {self.damage} and durability {self.durability}'

@dataclass
class Sword(Weapon):
    length: float = 100.0
    def __str__(self):
        return f'{self.quality} sword {self.name} with length {self.length}'

@dataclass
class Wand(Weapon):
    weapon_type = 'Wand'
    item_type = 'Wand'
    range: float = 20.0
    def __str__(self):
        return f'{self.quality} wand {self.name} with range {self.range} and durability {self.durability}'

@dataclass
class Armor(Item):
    character_class: str = 'Warrior'
    defense: float = 0.1
    health: float = 20.0
    agility: float = -5.0
    strength: float = 10.0
    durability: float = 100.0
    quality: str = 'Common'
    slot: str = 'chest'
    def __str__(self):
        return f'Armor {self.name} with defense {self.defense}'

@dataclass
class Shield(Weapon):
    weapon_type = 'Shield'
    def __str__(self):
        return f'Shield {self.name}'

@dataclass
class Food(Item):
    name: str = 'Food'
    health: float = 5.0
    saturation: float = 2.0
    item_type: str = 'Food'
    def __str__(self):
        return f'Food {self.name} with health {self.health} and saturation {self.saturation}'

@dataclass
class Potion(Food):
    name: str = 'Potion'
    description: str = ''
    quality: str = 'Common'
    potion_type: str = 'Heal'
    value: float = 10.0
    item_type: str = 'Potion'
    def __str__(self):
        return f'Potion {self.name} with health {self.health} and saturation {self.saturation}'


class InteractableObject: # A crafting station
    def __init__(self, name, description, object_type: str):
        self.name = name
        self.description = description
        self.object_type = object_type

class Companion: # A companion is a non-player character that can assist the player in combat
    def __init__(self, name: str, companion_class: str, health: float, damage: float, skills: list['Skill']):
        self.name = name
        self.companion_class = companion_class
        self.health = health
        self.damage = damage
        self.skills = skills

    def assist(self, target):
        """Companion assists the player in combat."""
        print(f"{self.name} assists by dealing {self.damage} damage to {target.name}!")
        target.take_damage(self.damage)

    def use_ability(self, ability, target=None):
        """Use one of the companion's abilities."""
        if ability in self.abilities:
            print(f"{self.name} uses {ability}!")
            # Define specific ability effects here
            if ability == "Heal":
                print(f"{self.name} heals their ally!")
            elif target:
                print(f"{self.name} attacks {target.name} with {ability}!")
        else:
            print(f"{self.name} doesn't have the ability '{ability}'.")

class Region: # A region is a collection of cities
    def __init__(self, name, description, resources, cities):
        self.name = name
        self.description = description
        self.resources = resources
        self.cities = cities
    def describe(self):
        """Describe the region."""
        print(f"Region: {self.name}")
        print(f"Description: {self.description}")
        print()

class Quest: 
    def __init__(self, name, region, giver, storyline, objectives, rewards, reputation: float = 0, gold: int = 10):
        self.name = name
        self.region = region
        self.giver = giver
        self.storyline = storyline
        self.objectives = objectives  # List of objectives
        self.current_objective = 0    # Start from the first objective
        self.completed = False
        self.rewards = rewards
        self.reputation = reputation
        self.gold = gold

    def give_rewards(self, player: 'Character'):
        """
        Give the player the rewards after the quest is completed.
        """
        if self.completed:
            for reward in self.rewards:
                if player.inventory.capacity - len(player.inventory.contents) >= 1:
                    player.inventory.add_item(reward)
                    print(f"{player.name} received reward: {reward.name}.")
                else:
                    player.storage.add_item(reward)
                if self.region in player.reputation:
                    player.reputation[self.region] += self.reputation
                else:
                    player.reputation[self.region] = self.reputation
                print(f"Player {player.name} gained {self.reputation} reputation in {self.region}.")
                player.gold += self.gold
                print(f"Player {player.name} gained {self.gold} gold.")
        else:
            print(f"Quest '{self.name}' is not completed. Rewards unavailable.")
    def __str__(self):
        return f"Quest: {self.name}, {self.storyline}, {self.objectives}, {self.rewards}"


class City:
    def __init__(self, name: str, region: Region, population: int, guards: int, faction: 'Faction', shops: list[str]):
        self.name = name
        self.region = region
        self.population = population
        self.shops = shops
        self.guards = guards # Combat power of the city
        self.faction = faction

class Inventory:
    def __init__(self, player: 'Character'=None, name: str='Inventory', capacity: int=20, contents: list[Item]=[]):
        self.name = name
        self.player = player
        self.capacity = capacity
        self.contents = contents
        self.known_recipes = {
            ("Iron Ore", "Wood"): {
                "result": Weapon(name="Iron Sword", description="A basic iron sword.", damage=15.0),
                "requirements": {"strength": 5, "crafting_level": 1},
                "required_station": "Forge",
                "experience": 25
            },
            ("Herbs", "Potion Bottle"): {
                "result": Potion(name="Healing Potion", description="Restores health.", potion_type="Health", value=20.0),
                "requirements": {"intelligence": 5},
                "required_station": "Alchemy Table",
                "experience": 10
            }
        }

    def discover_recipe(self, recipe: tuple, result: Item, requirements: dict = None):
        """Discover a new crafting recipe."""
        if recipe not in self.known_recipes:
            self.known_recipes[recipe] = {"result": result, "requirements": requirements or {}}
            print(f'New recipe discovered: {result.name}')
            print()
        else:
            print(f'Recipe for {result.name} already known.')
            print()
    def check_crafting_requirements(self, requirements: dict, player: 'Character') -> bool:
        """Check if the player meets the requirements to craft an item."""
        for stat, value in requirements.items():
            if stat == "character_class" and player.character_class != value:
                print(f"Cannot craft this item. Requires {value} class. You are a {player.character_class}.")
                return False
            elif stat == "crafting_level" and player.crafting_level < value:
                print(f"Cannot craft this item. Requires crafting level {value}. Current: {player.crafting_level}.")
                return False
            elif stat in vars(player) and getattr(player, stat, 0) < value:
                print(f"Cannot craft this item. Requires {stat} >= {value}. Current: {getattr(player, stat, 0)}.")
                return False
        return True

    def calculate_crafted_quality(self, recipe: tuple) -> str:
        """Calculate the quality of the crafted item based on the materials used."""
        material_quality = [item.quality for item in self.contents if item.name in recipe]
        if all(q == "Legendary" for q in material_quality):
            return "Legendary"
        elif all(q in ("Epic", "Legendary") for q in material_quality):
            return "Epic"
        elif all(q in ("Rare", "Epic", "Legendary") for q in material_quality):
            return "Rare" if any(q == "Rare" for q in material_quality) else "Epic"
        return "Common"


    def craft(self, recipe: tuple, player: 'Character', station: str = None):
        """Craft an item using the given recipe."""
        # Check if the recipe is known
        if recipe not in self.known_recipes:
            print("You don't know this recipe yet. Try discovering it first.")
            return

        # Retrieve recipe details
        recipe_details = self.known_recipes[recipe]
        required_resources = recipe
        crafting_requirements = recipe_details["requirements"]
        result_item = recipe_details["result"]
        required_station = recipe_details.get("required_station", None)
        crafting_experience = recipe_details.get("experience", 0)

        # Check crafting station
        if required_station and station != required_station:
            print(f"This recipe requires a {required_station}. You are using a {station}.")
            return

        # Validate crafting requirements (stats, level, class, etc.)
        if not self.check_crafting_requirements(crafting_requirements, player):
            return

        # Validate required resources
        if not all(any(item.name == material for item in self.contents) for material in required_resources):
            print("You lack the necessary resources to craft this item.")
            return

        # Calculate result item quality based on material quality
        crafted_quality = self.calculate_crafted_quality(required_resources)
        result_item.quality = crafted_quality

        # Remove used resources from inventory
        for material in required_resources:
            for item in self.contents:
                if item.name == material:
                    self.contents.remove(item)
                    break

        
        if self.capacity < len(self.contents) + 1:
            self.add_item(result_item)
            print(f"Crafted a {crafted_quality} {result_item.name}!")
            player.gain_crafting_experience(crafting_experience)
        else:
            player.storage.add_item(result_item)
            print(f"Crafted a {crafted_quality} {result_item.name}! Stored in storage.")

    def add_item(self, item: Item):
        """Add an item to the inventory."""
        if self.capacity >= len(self.contents) + 1:
            self.contents.append(item)
            print(f'Added {item.name} to inventory.')
            item.trigger_quest(self.player)
        else:
            self.player.storage.add_item(item)
            print(f'Added {item.name} to storage because inventory is full.')
        while self.capacity < len(self.contents):
            self.player.storage.add_item(self.contents.pop())

    def remove_item(self, item: Item):
        """Remove an item from the inventory."""
        if item in self.contents:
            self.contents.remove(item)
            return item
        else:
            print('Item not in inventory')
            print()
            return None
    def __str__(self):
            return f'{self.name} with capacity {self.capacity} and contents {[str(i) for i in self.contents]}'
    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index < len(self.contents):
            item = self.contents[self._index]
            self._index += 1
            return item
        else:
            raise StopIteration
    def __len__(self):
        return len(self.contents)
    def take_item_from_storage(self, item: Item):
        """Take an item from storage and add it to the inventory."""
        if item in self.player.storage.contents:
            self.player.storage.contents.remove(item)
            self.add_item(item)
        else:
            print('Item not in storage')
            print()
            return None
    def deposit_item_to_storage(self, item: Item):
        """Deposit an item from the inventory to storage."""
        if item in self.contents:
            self.contents.remove(item)
            self.player.storage.add_item(item)
        else:
            print('Item not in inventory')
            print()
            return None

class Storage: # Not inventory, storage is endless and can be accessed from anywhere. Will be reworked later.
    def __init__(self, name: str, contents: list[Item] = None):
        self.name = name
        self.contents = contents or []
    def __str__(self):
        return f'{self.name} with contents {[str(i) for i in self.contents]}'
    def add_item(self, item: Item):
        """Add an item to the storage."""
        self.contents.append(item)
        print(f'Added {item.name} to storage.')

class Character: # Player
    def __init__(self, name: str, inventory: Inventory, character_class: str, max_health: float=100.0, strength: float=10.0, intelligence: float=10.0, agility: float=10.0, luck: float=10.0,  experience: float=0.0, level: int=1, saturation: float=10.0, max_mana: float=15.0, quests:list[Quest]=[], reputation: dict[City: int]={}, completed_quests: list[Quest]=[], region: Region=None, city: City=None, race: str='Human', special_abilities: list[str]=[], achievements: list[str]=[], skills: dict[str: list[int, str, int]]=[], crafting_level: int = 1, crafting_experience: float = 0, gold: int = 100, storage: Storage=Storage(name='Storage')):
        self.skills = skills
        self.achievements = achievements
        self.name = name
        self.race = race
        self.max_health = max_health
        self.inventory = inventory
        self.character_class = character_class
        self.strength = strength
        self.intelligence = intelligence
        self.agility = agility
        self.luck = luck
        self.experience = experience
        self.level = level
        self.right_hand = None
        self.left_hand = None
        self.armor_chest = None
        self.armor_head = None
        self.armor_legs = None
        self.armor_feet = None
        self.defense = 10.0
        self.damage = 5.0
        self.city = city
        self.respawn_time = 10
        self.reputation = reputation
        self.completed_quests = completed_quests
        self.saturation = saturation
        self.region = region
        self.special_abilities = special_abilities
        self.health = self.max_health
        self.max_saturation = 10.0
        self.max_mana = max_mana * 5 if character_class == 'Mage' else max_mana * 3 if character_class == 'Shaman' else max_mana * 0.75 if character_class == 'Rogue' else max_mana
        self.mana = self.max_mana
        self.quests = quests
        self.alive = True
        self.crafting_level = crafting_level
        self.crafting_experience = crafting_experience
        self.gold = gold
        self.storage = storage
    def gain_crafting_experience(self, exp: float):
        """"Gain crafting experience."""
        self.crafting_experience += exp
        print(f"{self.name} gained {exp} crafting experience.")
        if self.crafting_experience >= self.crafting_level * 100:
            self.level_up_crafting()
            return
        print()
    def accept_quest(self, quest: Quest):
        """Accept a quest."""
        if quest in self.quests or quest in self.completed_quests:
            print(f"Quest '{quest.name}' is already accepted or completed.")
            return
        self.quests.append(quest)
        print(f"Quest '{quest.name}' accepted.")

    def complete_quest(self, quest: Quest):
        """Complete a quest."""
        quest.completed = True
        if quest in self.quests and quest.completed:
            self.quests.remove(quest)
            self.completed_quests.append(quest)
            print(f"Quest '{quest.name}' marked as completed!")
            quest.give_rewards(self)
        else:
            print(f"Quest '{quest.name}' cannot be marked complete.")

    def level_up_crafting(self):
        """Level up in crafting."""
        self.crafting_level += 1
        self.crafting_experience = 0
        print(f"{self.name} leveled up in crafting to level {self.crafting_level}!")
        print()

    def equip_weapon(self, weapon: Weapon, hand: str = 'right'):
        """Equip a weapon."""
        if not self.check_requirements(weapon):
            return
        if weapon.character_class != self.character_class:
            print(f"{weapon.name} cannot be equipped by a {self.character_class}. Required: {weapon.character_class}.")
            print()
            return
        if weapon in self.inventory.contents:
            if hand == 'right':
                if self.right_hand:
                    self.disequip_weapon(self.right_hand)
                self.right_hand = weapon
                self.damage += weapon.damage
            elif hand == 'left':
                if self.left_hand:
                    self.disequip_weapon(self.left_hand)
                self.left_hand = weapon
                self.damage += weapon.damage
        else:
            print('Weapon not in inventory')
            print()
    def check_requirements(self, item: Item) -> bool:
        """Check if the player meets the requirements to use the item."""
        if not item.requirements:
            return True
        for stat, required_value in item.requirements.items():
            if getattr(self, stat, 0) < required_value:
                print(f"Cannot use {item.name}. Requires {stat} {required_value}. Current: {getattr(self, stat, 0)}.")
                print()
                return False
        return True

    def increase_reputation(self, city: str, amount: int):
        """Increase reputation with a city."""
        if city not in self.reputation:
            self.reputation[city] = 0
        self.reputation[city] += amount
        print(f'Reputation with {city} increased by {amount}.')
        print()
    
    def decrease_reputation(self, city: str, amount: int):
        """Decrease reputation with a city."""
        if city not in self.reputation:
            self.reputation[city] = 0
        self.reputation[city] -= amount
        print(f'Reputation with {city} decreased by {amount}.')
        print()
    
    def get_reputation(self, city: str):
        """Get reputation with a city."""
        return self.reputation.get(city, 0)

    def disequip_weapon(self, weapon: Weapon):
        """Disequip a weapon."""
        if weapon in self.inventory.contents:
            if self.right_hand == weapon:
                self.right_hand = None
                self.damage -= weapon.damage
            elif self.left_hand == weapon:
                self.left_hand = None
                self.damage = weapon.damage
            else:
                print('Weapon not equipped')
                print()
        else:
            print('Weapon not in inventory')
            print()
    def learn_skill(self, skill: str, cost: int, skill_type: str, value: int):
        """Learn a skill."""
        if skill in self.skills:
            print(f'{self.name} already knows {skill}')
            print()
        else:
            self.skills[skill] = [cost, skill_type, value]
            print(f'{self.name} learned {skill}') 
            print()
    def use_skill(self, skill: str, target: 'Character'):
        """Use a skill."""
        if skill in self.skills:
            if self.mana >= self.skills[skill][0]:
                self.mana -= self.skills[skill][0]
                if self.skills[skill][1] == 'heal':
                    target.health += self.skills[skill][2]
                    if target.health > target.max_health:
                        target.health = target.max_health
                    print(f'{self.name} used {skill} on {target.name} and healed them for {self.skills[skill][2]} health')
                    print()
                elif self.skills[skill][1] == 'damage':
                    target.health -= self.skills[skill][2]
                    if target.health < 0:
                        target.health = 0
                    print(f'{self.name} used {skill} on {target.name} and dealt {self.skills[skill][2]} damage')
                    print()
                elif self.skills[skill][1] == 'defense':
                    self.defense += self.skills[skill][2]
                    print(f'{self.name} used {skill} and increased their defense by {self.skills[skill][2]}')
                    print()
            else:
                print(f'{self.name} does not have enough mana to use {skill}')
                print()
        else:
            print(f'{self.name} does not know {skill}')
            print()
    def equip_armor(self, armor: Armor):
        """Equip an armor."""
        if not self.check_requirements(armor):
            return
        if armor.character_class != self.character_class:
            print(f"{armor.name} cannot be equipped by a {self.character_class}. Required: {armor.character_class}.")
            print()
            return
        if armor in self.inventory.contents:
            if armor.slot == 'chest':
                self.armor_chest = armor
                if self.armor_chest and self.armor_chest != armor:
                    self.disequip_armor(self.armor_chest)
                self.defense += armor.defense
                if self.health == self.max_health:
                    self.health += armor.health
                self.max_health += armor.health
                self.strength += armor.strength
                self.agility += armor.agility
                print(f'{armor.name} equipped')
                print()
            elif armor.slot == 'head':
                if self.armor_head and self.armor_head != armor:
                    self.disequip_armor(self.armor_head)
                self.armor_head = armor
                self.defense += armor.defense
                if self.health == self.max_health:
                    self.health += armor.health
                self.max_health += armor.health
                self.strength += armor.strength
                self.agility += armor.agility
                print(f'{armor.name} equipped')
                print()
            elif armor.slot == 'legs':
                if self.armor_legs and self.armor_legs != armor:
                    self.disequip_armor(self.armor_legs)
                self.armor_legs = armor
                self.defense += armor.defense
                if self.health == self.max_health:
                    self.health += armor.health
                self.max_health += armor.health
                self.strength += armor.strength
                self.agility += armor.agility
                print(f'{armor.name} equipped')
                print()
            elif armor.slot == 'feet':
                if self.armor_feet and self.armor_feet != armor:
                    self.disequip_armor(self.armor_feet)
                self.armor_feet = armor
                self.defense += armor.defense
                if self.health == self.max_health:
                    self.health += armor.health
                self.max_health += armor.health
                self.strength += armor.strength
                self.agility += armor.agility
                print(f'{armor.name} equipped')
                print()
            else:
                print('Invalid armor slot')
                print()
        else:
            print('Armor not in inventory')
            print()
    def to_city(self, city: City):
        """Travel to a city."""
        if self.city == city:
            print(f'{self.name} is already in the city {city.name}')
            print()
        elif city in self.region.cities:
            self.city = city
            print(f'{self.name} is now in the city {city.name}')
            print()
        else:
            print(f'{self.name} is cannot enter {city.name} (need to travel the region {self.region} first)')
    def disequip_armor(self, armor: Armor):
        """Disequip an armor."""
        if armor in self.inventory.contents:
            if armor.character_class == self.character_class:
                if self.armor_chest == armor:
                    self.armor_chest = None
                    self.defense -= armor.defense
                    if self.health == self.max_health:
                        self.health -= armor.health
                    self.max_health -= armor.health
                    self.strength -= armor.strength
                    self.agility -= armor.agility
                    print(f'{armor.name} disequipped')
                    print()
                elif self.armor_head == armor:
                    self.armor_head = None
                    self.defense -= armor.defense
                    if self.health == self.max_health:
                        self.health -= armor.health
                    self.max_health -= armor.health
                    self.strength -= armor.strength
                    self.agility -= armor.agility
                    print(f'{armor.name} disequipped')
                    print()
                elif self.armor_legs == armor:
                    self.armor_legs = None
                    self.defense -= armor.defense
                    if self.health == self.max_health:
                        self.health -= armor.health
                    self.max_health -= armor.health
                    self.strength -= armor.strength
                    self.agility -= armor.agility
                    print(f'{armor.name} disequipped')
                    print()
                elif self.armor_feet == armor:
                    self.armor_feet = None
                    self.defense -= armor.defense
                    if self.health == self.max_health:
                        self.health -= armor.health
                    self.max_health -= armor.health
                    self.strength -= armor.strength
                    self.agility -= armor.agility
                    print(f'{armor.name} disequipped')
                    print()
                else:
                    print('Armor not equipped')
                    print()
    def attack(self, target: 'Mob'):
        """Attack a target."""
        is_critical = randint(1, 100) <= self.luck
        damage = self.damage * (2 if is_critical else 1)
        if self.character_class == 'Warrior' or self.character_class == 'Paladin' or self.character_class == 'Rogue' or self.character_class == 'Berserker' or self.character_class == 'Knight':
            damage += round(damage * self.strength / 100, 2)
        elif self.character_class == 'Mage' or self.character_class == 'Sorcerer' or self.character_class == 'Wizard' or self.character_class == 'Necromancer':
            damage += round(damage * self.intelligence / 100, 2)
        else:
            damage += round(damage * self.agility / 100, 2)
        print(f'{self.name} attacks {target.name}')
        target.take_damage(damage, attacker=self)

        if self.right_hand:
            self.right_hand.durability -= 1
            if self.right_hand.durability <= 0:
                print(f"{self.right_hand.name} has broken!")
                if not self.left_hand:
                    print()
                self.inventory.remove_item(self.right_hand)
                self.disequip_weapon(self.right_hand)
        if self.left_hand:
            self.left_hand.durability -= 1
            if self.left_hand.durability <= 0:
                print(f"{self.left_hand.name} has broken!")
                print()
                self.inventory.remove_item(self.left_hand)
                self.disequip_weapon(self.left_hand)

        self.saturation -= 0.5
    def consume(self, item: Item):
        """Consume an item."""
        if not self.check_requirements(item):
            return
        if item in self.inventory.contents:
            print(item.item_type)
            if item.item_type == 'Potion': # potion is a separate class but depends on Item
                if item.potion_type == 'Health':
                    self.health += item.value
                elif item.potion_type == 'Strength':
                    self.strength += item.value
                elif item.potion_type == 'Agility':
                    self.agility += item.value
                elif item.potion_type == 'Defense':
                    self.defense += item.value
                elif item.potion_type == 'Mana':
                    self.mana += item.value
                if self.health > self.max_health:
                    self.health = self.max_health
                if self.mana > self.max_mana:
                    self.mana = self.max_mana
                print(f'{self.name} consumed {item.name} ({item.potion_type}). Health: {self.health}, Mana: {self.mana}')
                print()
            elif item.item_type == 'Food':
                self.saturation += item.saturation
                self.health += item.health
                if self.health > self.max_health:
                    self.health = self.max_health
                if self.saturation > self.max_saturation:
                    self.saturation = self.max_saturation
                print(f'{self.name} consumed {item.name}. Health: {self.health}, saturation: {self.saturation}')
                print()
            else:
                print('Invalid item')
                print()
        else:
            print(f'{item.name} not found in inventory.')
            print()
    def use_item(self, item: Item):
        """Use an item."""
        if item in self.inventory.contents:
            if isinstance(item, Weapon):
                self.equip_weapon(item)
            elif isinstance(item, Armor):
                self.equip_armor(item, item.slot)
        else:
            print('Item not in inventory')
            print()
    def take_damage(self, damage: float) -> bool:
        """Take damage."""
        __agility = randint(30, 100)
        if self.right_hand is not None:
            __shield = randint(0, 10) if self.right_hand.weapon_type == 'Shield' else 11
        else:
            __shield = 11
        if self.agility > __agility or __shield < 1:
            print(f'{self.name} dodged the attack' if self.agility > __agility else f'{self.name} blocked the attack')
            print()
        else:
            if self.defense > 95:
                self.defense = 95
            damage = round(damage * (1 - self.defense / 100), 2)
            self.health -= damage
            print(f'{self.name} took {damage} damage')
            print(f'{self.name} has {self.health if self.health >= 0 else 0} health left')
            if self.health > 0:
                print()
        if self.health <= 0:
                print(f'{self.name} died')
                print()
                self.die()
                return True
        self.saturation -= 0.5
    def die(self):
        """Die."""
        self.health = 0
        self.alive = False
        print(f"{self.name} is dead and will respawn in {self.respawn_time} seconds.")
        lost_experience = self.level * 10
        print(f"{self.name} has lost {lost_experience} experience upon death.")
        self.experience -= lost_experience
        if self.experience < 0:
            if self.level > 1:
                self.level -= 1
                self.experience = self.level * 100 - min(abs(self.experience), self.level * 100)
            else:
                self.level = 1
                self.experience = 0
        print(f"{self.name}'s experience is now {self.level}lvl, {self.experience}xp.")
        sleep(self.respawn_time) # Stops the game for the respawn time
        print()
        self.respawn()
    def respawn(self):
        """Respawn."""
        self.health = self.max_health
        self.mana = self.max_mana
        self.saturation = 10
        self.alive = True
        print(f"{self.name} has respawned.")
        print()
    def regenerate(self, health_rate: float=1, mana_rate=1):
        """Regenerate health and mana."""
        if self.health < self.max_health:
            self.health += health_rate
            if self.health > self.max_health:
                self.health = self.max_health
        if self.mana < self.max_mana:
            self.mana += mana_rate
            if self.mana > self.max_mana:
                self.mana = self.max_mana

    def gain_experience(self, exp_amount):
        """Gain experience."""
        self.experience += exp_amount
        print(f'{self.name} gained {exp_amount} experience')
        if self.experience >= self.level * 100:
            self.level_up()

    def level_up(self):
        """Level up."""
        self.level += 1
        self.strength += 2
        self.health += 10
        self.mana += 5
        self.max_health += 10
        self.max_mana += 5
        if self.agility > 95:
            self.agility = 95
        print(f'{self.name} leveled up to level {self.level}!')
        self.experience = self.experience - (self.level * 100)
        if self.experience < 0:
            self.experience = 0
        if self.experience > self.level * 100:
            self.level_up()
            return
        print()

    def interact(self, other: InteractableObject, ingredients: tuple = None):
        """Interact with an object."""
        if isinstance(other, InteractableObject):
            match other.object_type:
                case 'Potion':
                    self.Inventory.craft(ingredients, other.object_type)
                case 'Weapon':
                    self.Inventory.craft(ingredients, other.object_type)
                case 'Armor':
                    self.Inventory.craft(ingredients, other.object_type)
                case _:
                    print('Invalid object')
                    print()
        else:
            print('Invalid object')
        
    def rest(self, seconds: int):
        """Rest for a number of seconds and regenerate health and mana."""
        for _ in range(5, seconds + 5):
            self.regenerate()
            sleep(1)
        print(f'{self.name} rested for {seconds} seconds.')
        print(f'{self.name} has {self.health} health and {self.mana} mana.')
        print()
    def unlock_achievement(self, achievement_name: str):
        """Unlock an achievement."""
        if achievement_name not in self.achievements:
            self.achievements.append(achievement_name)
            print(f"Achievement unlocked: {achievement_name}")
            print()
    def travel_to_region(self,  region: Region):
        """Travel to a region."""
        self.region = region
        print(f"{self.name} traveled to {region.name}.")

class Skill: # To not store skills in a tuple because it is inconvenient to use.
    def __init__(self, skill_type: str, value: float, cost: float):
        self.skill_type = skill_type
        self.value = value
        self.cost = cost
    def level_up(self):
        """Level up."""
        self.value += 3
        self.cost += 2

class Mob: # Any enemy that can be killed.
    def __init__(
        self,
        name: str,
        health: float = 100.0,
        max_health: float = 100.0,
        damage: float = 10.0,
        strength: float = 10.0,
        level: int = 1,
        mana: float = 100.0,
        max_mana: float = 100.0,
        defense: float = 10.0,
        evil: bool = True,
        mob_class: str = 'Warrior',
        race: str = 'Goblin',
        gender: str = 'Male',
        experience: float = 0.0,
        alive: bool = True,
        mob_type: str = 'Monster',
        skills: dict = None,
        loot: Item = None,  # Reward for defeating the mob
        trigger: Quest = None,
        is_boss: bool = False,
    ):
        self.name = name
        self.health = health
        self.max_health = max_health
        self.damage = damage
        self.strength = strength
        self.level = level
        self.mana = mana
        self.max_mana = max_mana
        self.defense = defense
        self.evil = evil
        self.mob_class = mob_class
        self.race = race
        self.gender = gender
        self.experience = experience
        self.alive = alive
        self.mob_type = mob_type
        self.skills = skills if skills is not None else {}
        self.loot = loot
        self.trigger = trigger
        self.is_boss = is_boss

    def __str__(self):
        return f'Mob {self.name} with health {self.health} and damage {self.damage}'

    def take_damage(self, damage: float, attacker: 'Character'):
        """Take damage."""
        if not self.alive:
            print(f"{self.name} is already dead.")
            return

        self.health -= damage
        print(f"{self.name} took {damage} damage. Remaining health: {max(self.health, 0)}.")

        if self.health <= 0:
            self.alive = False
            print(f"{self.name} has been slain!")        
            attacker.complete_quest(self.trigger)
            # Grant reward if available
            if self.loot:
                print(f"{self.name} dropped {self.loot.name}.")
                if attacker.inventory.capacity - len(attacker.inventory.contents) >= 1:
                    attacker.inventory.add_item(self.loot)
                    print(f'You have gained {self.loot.name}!')
                else:
                    attacker.storage.add_item(self.loot)
                    print(f'ou have no room in your inventory for {self.loot.name}, so it has been placed in your storage.')

            # Grant experience
            attacker.gain_experience(self.experience)

    def attack(self, target: 'Character'):
        """Attack a target."""
        if self.alive:
            print(f'{self.name} attacks {target.name}')
            target.take_damage(self.damage)
            if not target.alive:
                self.health = self.max_health
                self.mana = self.max_mana

    def use_skill(self, target: 'Character'):
        """Use a skill."""
        if self.alive:
            if self.health < self.max_health / 2:
                for i in self.skills:
                    if self.skills[i].skill_type == 'Heal':
                        self.health += self.skills[i].value
                        self.mana -= self.skills[i].cost
                        print(f'{self.name} used skill {i} and healed for {self.mana}')
                        print()
                        if self.health > self.max_health:
                            self.health = self.max_health
                        if self.mana < 0:
                            self.mana = 0
                        return
            else:
                for i in self.skills:
                    if self.skills[i].skill_type == 'Damage':
                        print(f'{self.name} used skill {i} on {target.name}')
                        target.take_damage(self.skills[i].value)
                        self.mana -= self.skills[i].cost
                        if self.mana < 0:
                            self.mana = 0
                        return

class WorldClock: # Do not used yet. Planning to add a day/night cycle with minor events.
    def __init__(self):
        self.day = 0
        self.time_of_day = "Morning"

    def advance_time(self):
        """Advance the time by one day."""
        self.day += 1
        if self.time_of_day == "Morning":
            self.time_of_day = "Afternoon"
        elif self.time_of_day == "Afternoon":
            self.time_of_day = "Evening"
        elif self.time_of_day == "Evening":
            self.time_of_day = "Night"
        else:
            self.time_of_day = "Morning"

    def print_day_info(self):
        """Print the current day and time of day."""
        print(f"Day {self.day}: {self.time_of_day}")
        print()

class QuestGiver: # NPC with quests
    def __init__(self, name: str, available_quests: list[Quest]):
        self.name = name
        self.available_quests = available_quests

    def give_quest(self, player: 'Character'):
        """Give a quest to the player."""
        for quest in self.available_quests:
            if quest not in player.quests and quest not in player.completed_quests:
                player.accept_quest(quest)
                print(f"{self.name} has given the quest: '{quest.name}'.")
                return
        print(f"{self.name} has no quests available for {player.name}.")

class Faction: # Do not used yet. Planning to add factions and influence with some unique buffs or debuffs.
    def __init__(self, name: str, description: str='', leader: Character=None, members: list[Character]=[]):
        self.name = name
        self.description = description
        self.leader = leader
        self.members = members
    def gain_influence(self, amount):
        """Increase the faction's influence."""
        self.influence += amount
        if self.influence > 100:
            self.influence = 100
        print(f"{self.name}'s influence increased to {self.influence}.")

    def lose_influence(self, amount):
        """Decrease the faction's influence."""
        self.influence -= amount
        if self.influence < 0:
            self.influence = 0
        print(f"{self.name}'s influence decreased to {self.influence}.")

quest1, quest2, quest3 = Quest(
        name="Slay the Bandit Leader",
        region="Vornak Wastelands",
        giver="Eldora, Warrior of the Warriors Order",
        storyline="A dangerous bandit leader has been terrorizing the region. End his reign of terror.",
        objectives=["Find the Bandit Camp", "Defeat the Bandit Leader"],
        rewards=[Weapon(name='Bandit Leader\'s Axe', description='A powerful axe wielded by the bandit leader.', quality='Legendary', damage=100.0)],
        reputation = 5,
        gold = 100
    ), Quest(
        name="Recover the Lost Relic",
        region="Eldoria",
        giver="Galen, Mage of the Mages Guild",
        storyline="An ancient relic was stolen by thieves and must be recovered before it falls into the wrong hands.",
        objectives=["Investigate the Theft", "Locate the Thieves' Hideout", "Recover the Relic"],
        rewards=["200 Gold", "Mage's Favor"],
    ), Quest(
        name="Save the Trapped Miners",
        region="Shattered Peaks",
        giver="Ironhold Miner Guild",
        storyline="A group of miners are trapped after a cave-in. Rescue them before supplies run out.",
        objectives=["Enter the Collapsed Mines", "Clear the Rubble", "Escort the Miners to Safety"],
        rewards=["300 Gold", "Free Access to Mines"],
    )
quests = [
    quest1, quest2, quest3
]

mob1, mob2, mob3, mob4 = Mob(name="Goblin Raider", health=50, damage=10, loot=Item('Goblin Spear'), level=3),Mob(name="Sand Wyrm", health=200, damage=25, loot=Item('Wyrm scale'), level=7),Mob(name="Forest Troll", health=300, damage=30, loot=Item("Troll Hide"), level=10),Mob(name="Dune Leviathan", health=1000, damage=50, loot=Item("Leviathan Claw"), level=20, is_boss=True, trigger=quest1),
mobs = [
    mob1, mob2, mob3, mob4
]

region1, region2, region3 = Region(
        name="Eldoria",
        description="A prosperous kingdom known for its magical wonders.",
        resources=["Magic Crystals", "Herbs", "Iron"],
        # dangers=["Bandits", "Wild Beasts"],
        cities=[],
    ),Region(
        name="Vornak Wastelands",
        description="A desolate desert filled with ancient ruins.",
        resources=["Obsidian Shards", "Rare Spices"],
        # dangers=["Sand Wyrms", "Bandits"],
        cities=[],
    ),Region(
        name="Shattered Peaks",
        description="A mountainous region where ancient mages once studied.",
        resources=["Dragon Ore", "Mana Stones"],
        # dangers=["Dragons", "Rock Elementals"],
        cities=[],
    ),
regions = [
    region1, region2, region3
]

# Generate Cities
cities = [
    City(
        name="Eldoria City",
        population=15000,
        guards=500,
        faction=Faction("Mages Guild"),
        shops=["Spell Tomes", "Potions", "Magic Weapons"],
        region=region1
    ),
    City(
        name="Ironhold",
        population=8000,
        guards=200,
        faction=Faction("Warriors Order"),
        shops=["Steel Weapons", "Armor", "Mining Equipment"],
        region=region2
    ),
    City(
        name="Crystal Cove",
        population=2000,
        guards=50,
        faction=Faction("Merchants Guild"),
        shops=["Jewelry", "Rare Crystals", "Luxury Goods"],
        region=region1
    ),
    City(
        name="Oasis Outpost",
        population=1000,
        guards=30,
        faction=Faction("Free Traders"),
        shops=["Spices", "Water Supplies", "Exotic Goods"],
        region=region3
    ),
]

for region in regions:
    for city in cities:
        if city.name in region.cities:
            region.cities.append(city)

