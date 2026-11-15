"""Deterministic integer allocation. Inputs use string identifiers and integer units."""


def validate(stock, recipes):
    if not stock or not recipes:
        raise ValueError('库存和链接组成不能为空')
    for sku, amount in stock.items():
        if not isinstance(sku, str) or not sku or type(amount) is not int or amount < 0:
            raise ValueError('库存编号须为非空字符串，数量须为非负整数')
    for link, recipe in recipes.items():
        if not isinstance(link, str) or not link or not recipe:
            raise ValueError('链接编号和组成不能为空')
        for sku, units in recipe.items():
            if sku not in stock or type(units) is not int or units <= 0:
                raise ValueError('单品须存在，每份用量须为正整数')


def check(stock, recipes, plan):
    validate(stock, recipes)
    if set(plan) != set(recipes):
        raise ValueError('计划必须准确覆盖所有链接')
    if any(type(n) is not int or n < 0 for n in plan.values()):
        raise ValueError('计划库存须为非负整数')
    used = {sku: 0 for sku in stock}
    for link, recipe in recipes.items():
        for sku, units in recipe.items():
            used[sku] += units * plan[link]
    rows = {sku: {'available': stock[sku], 'used': used[sku],
                  'remaining': stock[sku] - used[sku],
                  'shortage': max(0, used[sku] - stock[sku])}
            for sku in stock}
    return {'passed': all(r['remaining'] >= 0 for r in rows.values()), 'items': rows}


def allocate(stock, recipes):
    validate(stock, recipes)
    remaining = dict(stock)
    plan = dict.fromkeys(recipes, 0)
    active = sorted(recipes)
    while active:
        active = [link for link in active if all(
            remaining[sku] >= units for sku, units in recipes[link].items())]
        if not active:
            break
        demand = dict.fromkeys(stock, 0)
        for link in active:
            for sku, units in recipes[link].items():
                demand[sku] += units
        rounds = min(remaining[sku] // units for sku, units in demand.items() if units)
        if rounds:
            for link in active:
                plan[link] += rounds
            for sku, units in demand.items():
                remaining[sku] -= rounds * units
        else:
            for link in active:
                if all(remaining[sku] >= units for sku, units in recipes[link].items()):
                    plan[link] += 1
                    for sku, units in recipes[link].items():
                        remaining[sku] -= units
    result = check(stock, recipes, plan)
    if not result['passed']:
        raise ArithmeticError('分配核对失败')
    return {'plan': plan, 'audit': result}


def related_links(recipes, targets):
    targets = set(targets)
    if not targets or not targets <= set(recipes):
        raise ValueError('目标链接不能为空且必须存在')
    touched = {sku for link in targets for sku in recipes[link]}
    return sorted(link for link, rec in recipes.items()
                  if link not in targets and touched.intersection(rec))


def allocate_partial(stock, recipes, targets, current):
    validate(stock, recipes)
    targets = set(targets)
    related = related_links(recipes, targets)
    if not set(related) <= set(current):
        raise ValueError('缺少相关链接当前库存: ' + ', '.join(set(related) - set(current)))
    touched = {sku for link in targets for sku in recipes[link]}
    fixed = dict.fromkeys(touched, 0)
    for link in related:
        n = current[link]
        if type(n) is not int or n < 0:
            raise ValueError('当前可售库存须为非负整数')
        for sku, units in recipes[link].items():
            if sku in touched:
                fixed[sku] += n * units
    residual = {sku: stock[sku] - fixed[sku] for sku in touched}
    if any(n < 0 for n in residual.values()):
        raise ValueError('固定链接已超出库存: ' + str({sku: -n for sku, n in residual.items() if n < 0}))
    result = allocate(residual, {link: recipes[link] for link in targets})
    result['fixed_usage'] = fixed
    result['required_current_links'] = related
    result['scope'] = '仅核对目标所用单品；非全店核对'
    return result
