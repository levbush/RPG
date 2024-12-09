from classes import *

running = True
while running:
    screen.fill(WHITE)  # Clear the screen

    if player.alive and not player.resting:
        for event in pygame.event.get():
            if event.type == QUIT:
                player.save_to_db()
                running = False
            elif event.type == KEYDOWN:

                if event.key == K_SPACE:
                    for mob in mobs:
                        if abs(player.x - mob.x) < 50 and abs(player.y - mob.y) < 50:
                            player.attack(mob)

                elif event.key == K_e:
                    render_inventory_menu(screen, player)

                elif event.key == K_q:
                    print("Quests:")
                    for quest in player.quests:
                        print(f" - {quest.name}")

                elif event.key == K_f:

                    for city in cities:
                        if abs(player.x - city.x) < 50 and abs(player.y - city.y) < 50:
                            city.enter(player, screen)

                    for npc in npcs:
                        if abs(player.x - npc.x) < 50 and abs(player.y - npc.y) < 50:
                            npc.interact(player)

                    for resource in world.resources:
                        if abs(player.x - resource.x) < 50 and abs(player.y - resource.y) < 50:
                            player.collect_resource(resource)

                elif event.key == K_m:
                    show_full_map = not show_full_map
                
                
    if not show_full_map:
        if player.alive and not player.resting:
            keys = pygame.key.get_pressed()
            player.move(keys)
            camera.center_on(player)

            screen_x, screen_y = camera.apply(player)

            pygame.draw.rect(screen, player.color, (screen_x, screen_y, 30, 30))

            font = pygame.font.Font(None, 24)
            name_surface = font.render(player.name, True, BLACK)
            screen.blit(name_surface, (screen_x, screen_y - 20))  # Render player name above

        for obj in mobs + npcs + cities:
            obj_screen_x = obj.x - camera.offset_x
            obj_screen_y = obj.y - camera.offset_y
            if -50 <= obj_screen_x <= SCREEN_WIDTH + 50 and -50 <= obj_screen_y <= SCREEN_HEIGHT + 50:
                screen_x, screen_y = camera.apply(obj)
                obj.draw_at(screen, (screen_x, screen_y))
            # Draw objects within the camera's view

        for resource in world.resources:
            res_x, res_y = resource.x - camera.offset_x, resource.y - camera.offset_y
            if -50 <= res_x <= SCREEN_WIDTH + 50 and -50 <= res_y <= SCREEN_HEIGHT + 50:
                if not resource.collected:
                    res_x, res_y = camera.apply(resource)
                    pygame.draw.circle(screen, (0, 255, 0), (res_x, res_y), 10)

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
        for resource in world.resources:
            if not resource.collected and abs(player.x - resource.x) < 50 and abs(player.y - resource.y) < 50:
                tooltip = f"Press F to collect {resource.resource_type}"

        if tooltip:
            tooltip_surface = font.render(tooltip, True, BLACK)
            screen.blit(tooltip_surface, (10, SCREEN_HEIGHT - 40))  # Show tooltip at the bottom of the screen
        draw_minimap(screen, world, player, mobs, cities, world.resources)
        logger.render(10, SCREEN_HEIGHT - 200)
    else:
        draw_full_world_map(screen, world, player, mobs, cities, world.resources)
    
    text_surface = font.render('Health: ' + str(player.health), True, RED)
    screen.blit(text_surface, (0, 0))
    text_surface = font.render('Mana: ' + str(player.mana), True, BLUE)
    screen.blit(text_surface, (0, 20))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
