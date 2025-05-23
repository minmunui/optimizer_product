def cal_pop_fitness(equation_inputs, pop):
    # Calculating the fitness value of each solution in the current population.
    # The fitness function calulates the sum of products between each input and its corresponding weight.
    fitness = numpy.sum(pop*equation_inputs, axis=1)
    return fitness

def select_mating_pool(pop, fitness, num_parents):
    # Selecting the best individuals in the current generation as parents for producing the offspring of the next generation.
    parents = numpy.empty((num_parents, pop.shape[1]))
    for parent_num in range(num_parents):
        max_fitness_idx = numpy.where(fitness == numpy.max(fitness))
        max_fitness_idx = max_fitness_idx[0][0]
        parents[parent_num, :] = pop[max_fitness_idx, :]
        fitness[max_fitness_idx] = -99999999999
    return parents

def crossover(parents, offspring_size):
    offspring = numpy.empty(offspring_size)
    # The point at which crossover takes place between two parents. Usually, it is at the center.
    crossover_point = numpy.uint8(offspring_size[1]/2)

    for k in range(offspring_size[0]):
        # Index of the first parent to mate.
        parent1_idx = k%parents.shape[0]
        # Index of the second parent to mate.
        parent2_idx = (k+1)%parents.shape[0]
        # The new offspring will have its first half of its genes taken from the first parent.
        offspring[k, 0:crossover_point] = parents[parent1_idx, 0:crossover_point]
        # The new offspring will have its second half of its genes taken from the second parent.
        offspring[k, crossover_point:] = parents[parent2_idx, crossover_point:]
    return offspring

def mutation(offspring_crossover, num_mutations=1):
    mutations_counter = numpy.uint8(offspring_crossover.shape[1] / num_mutations)
    # Mutation changes a number of genes as defined by the num_mutations argument. The changes are random.
    for idx in range(offspring_crossover.shape[0]):
        gene_idx = mutations_counter - 1
        for mutation_num in range(num_mutations):
            # The random value to be added to the gene.
            random_value = numpy.random.uniform(-1.0, 1.0, 1)
            offspring_crossover[idx, gene_idx] = offspring_crossover[idx, gene_idx] + random_value
            gene_idx = gene_idx + mutations_counter
    return offspring_crossover


if __name__ == "__main__":
    import numpy
    """
    The y=target is to maximize this equation ASAP:
        y = w1x1+w2x2+w3x3+w4x4+w5x5+6wx6
        where (x1,x2,x3,x4,x5,x6)=(4,-2,3.5,5,-11,-4.7)
        What are the best values for the 6 weights w1 to w6?
        We are going to use the genetic algorithm for the best possible values after a number of generations.
    """

    # Inputs of the equation.
    equation_inputs = [4, -2, 3.5, 5, -11, -4.7]

    # Number of the weights we are looking to optimize.
    num_weights = len(equation_inputs)

    """
    Genetic algorithm parameters:
        Mating pool size
        Population size
    """
    sol_per_pop = 8
    num_parents_mating = 4

    # Defining the population size.
    pop_size = (sol_per_pop,
                num_weights)  # The population will have sol_per_pop chromosome where each chromosome has num_weights genes.
    # Creating the initial population.
    new_population = numpy.random.uniform(low=-4.0, high=4.0, size=pop_size)
    print(new_population)

    """
    new_population[0, :] = [2.4,  0.7, 8, -2,   5,   1.1]
    new_population[1, :] = [-0.4, 2.7, 5, -1,   7,   0.1]
    new_population[2, :] = [-1,   2,   2, -3,   2,   0.9]
    new_population[3, :] = [4,    7,   12, 6.1, 1.4, -4]
    new_population[4, :] = [3.1,  4,   0,  2.4, 4.8,  0]
    new_population[5, :] = [-2,   3,   -7, 6,   3,    3]
    """

    best_outputs = []
    num_generations = 1000
    for generation in range(num_generations):
        print("Generation : ", generation)
        # Measuring the fitness of each chromosome in the population.
        fitness = cal_pop_fitness(equation_inputs, new_population)
        print("Fitness")
        print(fitness)

        best_outputs.append(numpy.max(numpy.sum(new_population * equation_inputs, axis=1)))
        # The best result in the current iteration.
        print("Best result : ", numpy.max(numpy.sum(new_population * equation_inputs, axis=1)))

        # Selecting the best parents in the population for mating.
        parents = select_mating_pool(new_population, fitness,
                                        num_parents_mating)
        print("Parents")
        print(parents)

        # Generating next generation using crossover.
        offspring_crossover = crossover(parents,
                                           offspring_size=(pop_size[0] - parents.shape[0], num_weights))
        print("Crossover")
        print(offspring_crossover)

        # Adding some variations to the offspring using mutation.
        offspring_mutation = mutation(offspring_crossover, num_mutations=2)
        print("Mutation")
        print(offspring_mutation)

        # Creating the new population based on the parents and offspring.
        new_population[0:parents.shape[0], :] = parents
        new_population[parents.shape[0]:, :] = offspring_mutation

    # Getting the best solution after iterating finishing all generations.
    # At first, the fitness is calculated for each solution in the final generation.
    fitness = cal_pop_fitness(equation_inputs, new_population)
    # Then return the index of that solution corresponding to the best fitness.
    best_match_idx = numpy.where(fitness == numpy.max(fitness))

    print("Best solution : ", new_population[best_match_idx, :])
    print("Best solution fitness : ", fitness[best_match_idx])

    import matplotlib.pyplot

    matplotlib.pyplot.plot(best_outputs)
    matplotlib.pyplot.xlabel("Iteration")
    matplotlib.pyplot.ylabel("Fitness")
    matplotlib.pyplot.show()