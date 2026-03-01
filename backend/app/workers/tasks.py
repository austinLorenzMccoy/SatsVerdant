from app.workers import celery_app
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app import models
from app.ml import waste_classifier, weight_estimator, quality_grader, fraud_detector
from app.services.reward_service import RewardService
from app.services.submission_service import SubmissionService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def classify_submission(self, submission_id: str) -> Dict[str, Any]:
    """
    Classify waste in submission image.
    """
    db: Session = SessionLocal()
    try:
        # Get submission
        submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")

        # TODO: Load image from S3
        # For MVP, simulate image loading
        image_bytes = b"fake image data"

        # Classify image
        classification = waste_classifier.classify_image(image_bytes)

        # Estimate weight
        weight_est = weight_estimator.estimate_weight(classification['waste_type'])

        # Grade quality
        quality = quality_grader.grade_image(image_bytes)

        # Fraud detection
        fraud_result = fraud_detector.detect_fraud(
            {
                'latitude': submission.latitude,
                'longitude': submission.longitude,
                'image_bytes': image_bytes
            },
            str(submission.user_id),
            db
        )

        # Update submission
        submission.ai_waste_type = classification['waste_type']
        submission.ai_confidence = classification['confidence']
        submission.ai_estimated_weight_kg = weight_est
        submission.ai_quality_grade = quality['grade']
        submission.fraud_score = fraud_result['score']
        submission.fraud_flags = fraud_result['flags']
        submission.status = "classified"

        db.commit()

        logger.info(f"Classified submission {submission_id}: {classification['waste_type']} ({classification['confidence']:.2%})")

        return {
            "submission_id": submission_id,
            "waste_type": classification['waste_type'],
            "confidence": classification['confidence'],
            "estimated_weight_kg": weight_est,
            "quality_grade": quality['grade'],
            "fraud_score": fraud_result['score'],
            "fraud_flags": fraud_result['flags'],
            "processing_time_ms": classification.get('processing_time_ms', 0)
        }

    except Exception as e:
        logger.error(f"Classification failed for {submission_id}: {str(e)}")
        db.rollback()
        raise self.retry(countdown=60, exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=5)
def pin_to_ipfs(self, submission_id: str) -> Dict[str, Any]:
    """
    Pin submission image to IPFS.
    """
    db: Session = SessionLocal()
    try:
        # Get submission
        submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")

        # TODO: Download from S3 and upload to IPFS
        # For MVP, simulate IPFS pinning
        ipfs_cid = f"QmFakeCID{submission_id[:8]}"
        thumbnail_cid = f"QmFakeThumb{submission_id[:8]}"

        # Update submission
        submission.image_ipfs_cid = ipfs_cid
        submission.thumbnail_ipfs_cid = thumbnail_cid
        submission.image_url = f"https://ipfs.io/ipfs/{ipfs_cid}"

        db.commit()

        logger.info(f"Pinned submission {submission_id} to IPFS: {ipfs_cid}")

        return {
            "submission_id": submission_id,
            "ipfs_cid": ipfs_cid,
            "thumbnail_ipfs_cid": thumbnail_cid,
            "ipfs_url": submission.image_url
        }

    except Exception as e:
        logger.error(f"IPFS pinning failed for {submission_id}: {str(e)}")
        db.rollback()
        raise self.retry(countdown=120, exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def mint_tokens(self, submission_id: str) -> Dict[str, Any]:
    """
    Mint waste tokens for approved submission.
    """
    db: Session = SessionLocal()
    try:
        # Get submission
        submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")

        # Calculate token amount
        reward_service = RewardService(db)
        tokens_to_mint = reward_service.calculate_reward_amount(
            submission.ai_waste_type,
            float(submission.ai_estimated_weight_kg or 0),
            submission.ai_quality_grade or 'C'
        )

        # Calculate carbon offset
        carbon_factor = {'plastic': 500, 'paper': 200, 'metal': 1200, 'organic': 100, 'electronic': 100}
        carbon_offset_g = int((submission.ai_estimated_weight_kg or 0) * carbon_factor.get(submission.ai_waste_type, 200))

        # TODO: Call blockchain contract to mint tokens
        # For MVP, simulate minting
        tx_id = f"0xFakeTx{submission_id[:8]}"

        # Update submission
        submission.tokens_minted = tokens_to_mint
        submission.carbon_offset_g = carbon_offset_g
        submission.mint_tx_id = tx_id
        submission.status = "minting"

        db.commit()

        # Enqueue transaction confirmation
        confirm_transaction.delay(tx_id, "submission", submission_id)

        logger.info(f"Minted {tokens_to_mint} tokens for submission {submission_id}")

        return {
            "submission_id": submission_id,
            "tx_id": tx_id,
            "tokens_minted": tokens_to_mint,
            "carbon_offset_g": carbon_offset_g,
            "status": "broadcasted"
        }

    except Exception as e:
        logger.error(f"Token minting failed for {submission_id}: {str(e)}")
        db.rollback()
        raise self.retry(countdown=60, exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=10)
def confirm_transaction(self, tx_id: str, entity_type: str, entity_id: str) -> Dict[str, Any]:
    """
    Confirm blockchain transaction and update entity status.
    """
    db: Session = SessionLocal()
    try:
        # TODO: Poll blockchain for transaction confirmation
        # For MVP, simulate confirmation after delay
        import time
        time.sleep(2)  # Simulate confirmation time

        # Update transaction record
        transaction = db.query(models.Transaction).filter(models.Transaction.tx_id == tx_id).first()
        if not transaction:
            transaction = models.Transaction(
                tx_id=tx_id,
                tx_type="mint" if entity_type == "submission" else "claim_reward",
                entity_type=entity_type,
                entity_id=entity_id,
                status="confirmed",
                block_height=12345,  # Fake block height
                confirmations=6
            )
            db.add(transaction)

        transaction.status = "confirmed"
        transaction.confirmed_at = db.func.now()

        # Update entity status
        if entity_type == "submission":
            submission = db.query(models.Submission).filter(models.Submission.id == entity_id).first()
            if submission:
                submission.status = "minted"
                submission.minted_at = db.func.now()

                # Create reward
                calculate_and_create_reward.delay(entity_id)

        elif entity_type == "reward":
            reward_service = RewardService(db)
            reward_service.update_reward_status(entity_id, "claimed", tx_id)

        db.commit()

        logger.info(f"Confirmed transaction {tx_id} for {entity_type} {entity_id}")

        return {
            "tx_id": tx_id,
            "status": "confirmed",
            "block_height": 12345,
            "confirmations": 6,
            "confirmed_at": str(db.func.now())
        }

    except Exception as e:
        logger.error(f"Transaction confirmation failed for {tx_id}: {str(e)}")
        db.rollback()
        raise self.retry(countdown=30, exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def calculate_and_create_reward(self, submission_id: str) -> Dict[str, Any]:
    """
    Calculate and create reward for minted submission.
    """
    db: Session = SessionLocal()
    try:
        # Get submission
        submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")

        # Create reward
        reward_service = RewardService(db)
        reward = reward_service.create_reward(
            str(submission.user_id),
            submission_id,
            submission.tokens_minted,
            conversion_rate=100000.0  # 1000 tokens = 0.01 sBTC
        )

        logger.info(f"Created reward {reward.id} for submission {submission_id}")

        return {
            "reward_id": str(reward.id),
            "sbtc_amount": str(reward.sbtc_amount),
            "status": "claimable"
        }

    except Exception as e:
        logger.error(f"Reward creation failed for {submission_id}: {str(e)}")
        db.rollback()
        raise self.retry(countdown=60, exc=e)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def distribute_reward(self, reward_id: str) -> Dict[str, Any]:
    """
    Distribute claimed reward to user wallet.
    """
    db: Session = SessionLocal()
    try:
        # Get reward
        reward = db.query(models.Reward).filter(models.Reward.id == reward_id).first()
        if not reward:
            raise ValueError(f"Reward {reward_id} not found")

        # TODO: Call blockchain to distribute sBTC
        # For MVP, simulate distribution
        tx_id = f"0xFakeRewardTx{reward_id[:8]}"

        # Update reward
        reward_service = RewardService(db)
        reward_service.update_reward_status(reward_id, "distributed", tx_id)

        logger.info(f"Distributed reward {reward_id} via transaction {tx_id}")

        return {
            "reward_id": reward_id,
            "tx_id": tx_id,
            "status": "distributed"
        }

    except Exception as e:
        logger.error(f"Reward distribution failed for {reward_id}: {str(e)}")
        db.rollback()
        raise self.retry(countdown=60, exc=e)
    finally:
        db.close()
