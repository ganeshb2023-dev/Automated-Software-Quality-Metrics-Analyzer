"""A deliberately messy module: high complexity and duplicated blocks."""


def process_order(order, user, inventory, log, notify, discount_code):
    total = 0
    if order is not None:
        if user is not None:
            if user.get("active"):
                for item in order.get("items", []):
                    if item["qty"] > 0:
                        if item["sku"] in inventory:
                            if inventory[item["sku"]] >= item["qty"]:
                                total += item["price"] * item["qty"]
                            else:
                                if log:
                                    log.append("insufficient stock")
                        else:
                            if log:
                                log.append("unknown sku")
                    else:
                        if log:
                            log.append("bad quantity")
            else:
                if log:
                    log.append("inactive user")
        else:
            if log:
                log.append("no user")
    else:
        if log:
            log.append("no order")

    if discount_code == "SAVE10":
        total = total * 0.9
    elif discount_code == "SAVE20":
        total = total * 0.8
    elif discount_code == "SAVE30":
        total = total * 0.7
    elif discount_code == "VIP":
        total = total * 0.5

    if notify:
        notify(total)

    return total


def process_refund(order, user, inventory, log, notify, discount_code):
    total = 0
    if order is not None:
        if user is not None:
            if user.get("active"):
                for item in order.get("items", []):
                    if item["qty"] > 0:
                        if item["sku"] in inventory:
                            if inventory[item["sku"]] >= item["qty"]:
                                total += item["price"] * item["qty"]
                            else:
                                if log:
                                    log.append("insufficient stock")
                        else:
                            if log:
                                log.append("unknown sku")
                    else:
                        if log:
                            log.append("bad quantity")
            else:
                if log:
                    log.append("inactive user")
        else:
            if log:
                log.append("no user")
    else:
        if log:
            log.append("no order")

    if notify:
        notify(-total)

    return -total
