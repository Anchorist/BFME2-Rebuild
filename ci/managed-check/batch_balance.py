"""Balance measured paired work and the fixed cost of starting each batch."""


def distribute(work, capacities, batch_size, batch_cost):
    loads = [batch_cost * ((n + batch_size - 1) // batch_size) for n in capacities]
    assigned = [[] for n in capacities]
    for weight, _, rows in work:
        i = min((i for i, n in enumerate(capacities) if len(assigned[i]) < n),
                key=lambda i: (loads[i], i))
        assigned[i].append((weight, rows))
        loads[i] += weight
    return assigned


def best_assignment(work, current, batch_size, batch_cost):
    """Try exact capacities around the even, batch-aligned floor."""
    def cost(groups):
        fees = [sum(w for w, _ in group) + batch_cost * ((len(group) + batch_size - 1) // batch_size)
                for group in groups]
        return max(fees), sum(fees)

    runners = len(current)
    floor = (len(work) // (runners * batch_size)) * batch_size
    extra = len(work) - floor * runners
    if not floor or batch_cost <= 0:
        return current
    first = (extra + batch_size - 1) // batch_size
    capacities = [[floor] * runners] if not extra else []
    for upgrades in range(max(1, first), min(extra, runners) + 1):
        pairs, surplus = divmod(extra, upgrades)
        larger = [floor + pairs + (i < surplus) for i in range(upgrades)]
        capacities.append([floor] * (runners - upgrades) + larger)
    best = current
    for shape in capacities:
        trial = distribute(work, shape, batch_size, batch_cost)
        if cost(trial) < cost(best):
            best = trial
    return best
