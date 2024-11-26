from classes import *

# Main Game Loop
running = True
while running:
    screen.fill(WHITE)  # Clear the screen

    # try:
        # Handle events
    if player.alive and not player.resting:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                # Open inventory
                if event.key == K_e:
                    render_inventory_menu(screen, player)
                # Display active quests
                elif event.key == K_q:
                    print("Quests:")
                    for quest in player.quests:
                        print(f" - {quest.name}")
                # Attack nearby mobs
                elif event.key == K_SPACE:
                    for mob in mobs:
                        if abs(player.x - mob.x) < 50 and abs(player.y - mob.y) < 50:
                            player.attack(mob)
                # Interact with cities and NPCs
                elif event.key == K_f:
                    # Interact with cities
                    for city in cities:
                        if abs(player.x - city.x) < 50 and abs(player.y - city.y) < 50:
                            city.enter(player, screen)
                    # Interact with NPCs
                    for npc in npcs:
                        if abs(player.x - npc.x) < 50 and abs(player.y - npc.y) < 50:
                            npc.interact(player)
                    # Interact with resources
                    for resource in world.resources:
                        if abs(player.x - resource.x) < 50 and abs(player.y - resource.y) < 50:
                            player.collect_resource(resource)
                elif event.key == K_m:  # Press 'M' to toggle the map view
                    show_full_map = not show_full_map   
    if not show_full_map:
        # Handle player movement
        if player.alive and not player.resting:
            keys = pygame.key.get_pressed()
            player.move(keys)
            camera.center_on(player)  # Center the camera on the player

            # Draw player
            screen_x, screen_y = camera.apply(player)

            # Check if the player is within screen bounds

            pygame.draw.rect(screen, player.color, (screen_x, screen_y, 30, 30))  # Green square for the player

            font = pygame.font.Font(None, 24)
            name_surface = font.render(player.name, True, BLACK)
            screen.blit(name_surface, (screen_x, screen_y - 20))  # Render player name above

        for obj in mobs + npcs + cities:
            # if is_within_view(camera, entity):
            obj_screen_x = obj.x - camera.offset_x
            obj_screen_y = obj.y - camera.offset_y
            if -50 <= obj_screen_x <= SCREEN_WIDTH + 50 and -50 <= obj_screen_y <= SCREEN_HEIGHT + 50:
                screen_x, screen_y = camera.apply(obj)
                # Render entity using screen coordinates
                obj.draw_at(screen, (screen_x, screen_y))

        # Draw resources
        for resource in world.resources:
            res_x, res_y = resource.x - camera.offset_x, resource.y - camera.offset_y
            if -50 <= res_x <= SCREEN_WIDTH + 50 and -50 <= res_y <= SCREEN_HEIGHT + 50:
                if not resource.collected:  # Skip collected resources
                    res_x, res_y = camera.apply(resource)
                    # Check if resource is within screen bounds
                    pygame.draw.circle(screen, (0, 255, 0), (res_x, res_y), 10)  # Green circle for resources

                    # Display resource name above the resource
                    resource_name_surface = font.render(f"{resource.resource_type} ({resource.quantity})", True, BLACK)
                    screen.blit(resource_name_surface, (res_x, res_y - 20))

        # Display interaction tooltip
        tooltip = None
        for mob in mobs:
            if abs(player.x - mob.x) < 50 and abs(player.y - mob.y) < 50:
                tooltip = f"Press SPACE to attack {mob.name}"
        for npc in npcs:
            if abs(player.x - npc.x) < 50 and abs(player.y - npc.y) < 50:
                tooltip = f"Press F to talk to {npc.name}"
        for city in cities:
            if abs(player.x - city.x) < 50 and abs(player.y - city.y) < 50:
                tooltip = f"Press F to enter {city.name}"
        for resource in world.resources:  # Check first 5 resources
            if not resource.collected and abs(player.x - resource.x) < 50 and abs(player.y - resource.y) < 50:
                tooltip = f"Press F to collect {resource.resource_type}"

        # Render tooltip if applicable
        if tooltip:
            tooltip_surface = font.render(tooltip, True, BLACK)
            screen.blit(tooltip_surface, (10, SCREEN_HEIGHT - 40))  # Show tooltip at the bottom of the screen
        draw_minimap(screen, world, player, mobs, cities, world.resources)
        # Render logger messages
        logger.render(10, SCREEN_HEIGHT - 200)
    else:
        # Draw the full map
        draw_full_world_map(screen, world, player, mobs, cities, world.resources)
    # Update the display
    pygame.display.flip()
    clock.tick(60)  # Limit to 60 FPS

    # except Exception as e:
    #     print(f"Error occurred: {e}")
    #     running = False

pygame.quit()
