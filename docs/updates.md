---
title: Documentation - To-Do, Enhancements, Explanations...
---

# To-Do

1. Youth player initialising and $k$ values for them to have bigger changes.
2. Extra scaling for players with _big influences_ like goals, assists.

---

# Enhancements needed

1. ELO Scaling
2. Youth player being too strong
3.

## 1. ELO Scaling

Right now, our program only considers **GD** (Goal Difference) when a player was on the pitch.
This could lead to a few issues

### Issues with current system

#### 1. Defenders will likely to have a better updates

Defenders usually spend more time on the pitch than attackers or midfielders.
Our new ELO rating for an individual player $i$ is calculated as following.

$$
R_{A_{i}}' = R_{A_i} + k_{A_i} \cdot ((q_{A_i} \cdot C_{A_i}) + ((1 - q_{A_i}) \cdot C_A \cdot \frac{M_{A_i}}{M_{\text{max}}}))
$$

Here, $q_{A_i}, k_{A_i}$ are independent to _MP_ (minutes played), so we know that the more minutes he plays on the match, the bigger change he gets.

This seems right at first, but since defenders generally spend more time on the pitch I am not really sure if this is entirely valid?

#### 2. Factors like goals not considered

Several factors should be considered when calculating individual ELO updates. This can include cases like

- A person who scored a goal, assist, gotten penalty kicks, or even free-kicks should be considered to have done more _impacts_ to the victory than a person who didn't
  - this _could_ lead to an issue defenders, midfielders generally having lower ELO updates than a attacker
- Yellow cards, or Red cards should be considered as a major downgrade factor for an ELO change.

> Basically, we should consider **match rating** as well

## 2. Youth players having too high initial ELO

Right now, when new player comes to the club with no previous ELO, we use two approach

1. Get his market value at that time, and use normal distribution to calculate which percentile he is located at, and do the same for ELO in reverse.
2. If he has no market value data, just average out his new teammates ELO.

### Counter example

There could be cases like, a new player $A$ joins _Real madrid CF_, and has no market value. Then his ELO value will be exceptionally high, which is quite not ideal because it is unlikely for a young, new player to have such high skills
