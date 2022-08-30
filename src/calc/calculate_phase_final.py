from _decimal import ROUND_HALF_DOWN
from decimal import Decimal
from calc.calculate_phase_base import (
    CalculatePhaseBase,
    BY_MIN_PAYMENT,
)
from model.baking_conf import MIN_PAYMENT_KEY
from model.reward_log import (
    TYPE_FOUNDER,
    TYPE_OWNER,
    TYPE_DELEGATOR,
    TYPE_FOUNDERS_PARENT,
    TYPE_OWNERS_PARENT
)

class CalculatePhaseFinal(CalculatePhaseBase):
    """
    --Final Stage: Payment Stage--

    At stage final, convert ratios to actual payment amounts.
    """

    def __init__(
        self, excluded_set_tob, excluded_set_tof, min_payment_amount=None
    ) -> None:
        super().__init__()

        self.min_payment_amount = min_payment_amount
        self.excluded_set_tob = excluded_set_tob
        self.excluded_set_tof = excluded_set_tof
        self.phase = 8 # should it be 6.5 ?

    def calculate(self, reward_data5, total_amount, adjustments={}):
        skipped_rewards = list(self.iterateskipped(reward_data5))
        rewards = list(self.filterskipped(reward_data5))

        amount_excluded = adjusted_amount_excluded = 0
        founders_parent_rl_idx = owners_parent_rl_idx = None
        # generate new rewards, rewards with the same address are merged
        new_rewards = []
        for rl in rewards:
            rl.amount = int(
                Decimal(rl.ratio * total_amount).to_integral_value(
                    rounding=ROUND_HALF_DOWN
                )
            )
            if adjustments and rl.address in adjustments.keys():
                rl.adjustment = max(-adjustments[rl.address], -rl.amount)
            else:
                rl.adjustment = 0
            rl.adjusted_amount = int(
                Decimal((rl.ratio * total_amount) + rl.adjustment).to_integral_value(
                    rounding=ROUND_HALF_DOWN
                )
            )
            rl.payable = rl.type in [TYPE_FOUNDER, TYPE_OWNER, TYPE_DELEGATOR]
            rl.service_fee_amount = int(
                Decimal(rl.service_fee_ratio * total_amount).to_integral_value(
                    rounding=ROUND_HALF_DOWN
                )
            )

            # exclude requested items
            if ((MIN_PAYMENT_KEY in self.excluded_set_tob
                or MIN_PAYMENT_KEY in self.excluded_set_tof)
                and rl.amount < self.min_payment_amount
            ):
                amount_excluded += rl.amount
                adjusted_amount_excluded += rl.adjusted_amount
                rl.skip(desc=BY_MIN_PAYMENT, phase=self.phase)
                rl.amount = 0
                rl.adjusted_amount = 0
                #rl.service_fee_amount = 0

            new_rewards.append(rl)

            # track last owners/founders parents
            if rl.type == TYPE_FOUNDERS_PARENT:
                founders_parent_rl_idx = len(new_rewards) - 1
            if rl.type == TYPE_OWNERS_PARENT:
                owners_parent_rl_idx = len(new_rewards) - 1

        # deal with payment amount excluded by min_payment_amt
        total_amount -= amount_excluded
        #if amount_excluded or adjusted_amount_excluded:
        #    if founders_parent_rl_idx and MIN_PAYMENT_KEY in self.excluded_set_tof:
        #        new_rewards[founders_parent_rl_idx].amount += amount_excluded
        #        new_rewards[founders_parent_rl_idx].adjusted_amount += adjusted_amount_excluded
        #    elif owners_parent_rl_idx and MIN_PAYMENT_KEY in self.excluded_set_tob:
        #        new_rewards[owners_parent_rl_idx].amount += amount_excluded
        #        new_rewards[owners_parent_rl_idx].adjusted_amount += adjusted_amount_excluded

        # add skipped rewards
        new_rewards.extend(skipped_rewards)

        return new_rewards, total_amount
